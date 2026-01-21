import re
from typing import Optional, Dict
from datetime import datetime, date

class DateNormalizer:
    """
    Standardizes chaotic date formats into YYYY-MM or YYYY.
    Supports English, Spanish, Short/Long months, and numerical formats.
    """
    
    MONTHS_MAP = {
        'ene': '01', 'enero': '01', 'jan': '01', 'january': '01',
        'feb': '02', 'febrero': '02', 'february': '02',
        'mar': '03', 'marzo': '03', 'march': '03',
        'abr': '04', 'abril': '04', 'apr': '04', 'april': '04',
        'may': '05', 'mayo': '05',
        'jun': '06', 'junio': '06', 'june': '06',
        'jul': '07', 'julio': '07', 'july': '07',
        'ago': '08', 'agosto': '08', 'aug': '08', 'august': '08',
        'sep': '09', 'septiembre': '09', 'september': '09',
        'oct': '10', 'octubre': '10', 'october': '10',
        'nov': '11', 'noviembre': '11', 'november': '11',
        'dic': '12', 'diciembre': '12', 'dec': '12', 'december': '12'
    }

    # Matches: "Mar 2023", "Marzo 2023", "03/2023", "2023-03", "2023"
    # Logic: Look for 4 digits (year) and a sequence of characters (month)
    DATE_PATTERN = re.compile(r'(\b[a-zA-ZáéíóúÁÉÍÓÚ]{3,10}\b|\b\d{1,2}\b)?[ \-/]*(\b\d{4}\b)', re.IGNORECASE)

    @classmethod
    def normalize(cls, raw_date: str) -> str:
        """
        Main entry point to normalize a date segment.
        Returns 'YYYY-MM', 'YYYY', or original if failure.
        """
        if not raw_date:
            return ""
            
        clean = raw_date.lower().strip()
        
        # 0. Handle 'Present'
        if any(w in clean for w in ['present', 'actualidad', 'presente', 'ahora', 'current']):
            return "Present"

        # 1. Try numerical formats first (YYYY-MM or MM/YYYY)
        # MM/YYYY
        mm_yyyy = re.search(r'(\d{1,2})[/\-](\d{4})', clean)
        if mm_yyyy:
            m = mm_yyyy.group(1).zfill(2)
            y = mm_yyyy.group(2)
            return f"{y}-{m}"
            
        # YYYY-MM
        yyyy_mm = re.search(r'(\d{4})[/\-](\d{1,2})', clean)
        if yyyy_mm:
            y = yyyy_mm.group(1)
            m = yyyy_mm.group(2).zfill(2)
            return f"{y}-{m}"

        # 2. Try Dictionary Search (Month Year)
        match = cls.DATE_PATTERN.search(clean)
        if match:
            month_part = match.group(1)
            year = match.group(2)
            
            if month_part:
                # Basic cleanup of month_part to handle abbreviations ending in dot
                month_key = month_part.replace('.', '').lower()
                if month_key in cls.MONTHS_MAP:
                    return f"{year}-{cls.MONTHS_MAP[month_key]}"
                
                # Check if it's a numeric month 1-12
                if month_key.isdigit():
                    m = int(month_key)
                    if 1 <= m <= 12:
                        return f"{year}-{str(m).zfill(2)}"
            
            # Just Year
            return year

        return raw_date # Return as is if we can't normalize, to avoid data loss

    @classmethod
    def extract_range(cls, text: str) -> tuple[str, str]:
        """
        Splits a string like 'Mar 2023 - Ago 2025' into two normalized dates.
        """
        # Common range separators
        parts = re.split(r'[\s\-\u2013\u2014]+', text)
        
        # Heuristic: If we have enough parts, find the mid-point or split by logic
        # For simplicity and robustness, we'll use a regex to find all dates
        all_dates = cls.DATE_PATTERN.findall(text)
        # findall returns list of tuples if capturing groups exist
        # We need the full segment. Let's use finditer.
        iter_dates = list(re.finditer(r'([a-zA-ZáéíóúÁÉÍÓÚ]{3,10}|\d{1,2})?[ \-/]*(\d{4})', text, re.IGNORECASE))
        
        if len(iter_dates) >= 2:
            start = cls.normalize(iter_dates[0].group(0))
            end_segment = text[iter_dates[0].end():].strip()
            # Check if 'Present' exists in the segment after the first date
            if any(w in end_segment.lower() for w in ['present', 'actualidad', 'presente', 'ahora']):
                return start, "Present"
            end = cls.normalize(iter_dates[1].group(0))
            return start, end
        elif len(iter_dates) == 1:
            start = cls.normalize(iter_dates[0].group(0))
            # Check for 'Present' anyway
            if any(w in text.lower() for w in ['present', 'actualidad', 'presente', 'ahora']):
                return start, "Present"
            return start, "Unknown"
            
        return "Unknown", "Unknown"
    @classmethod
    def parse_to_date(cls, raw_date: str, is_end_date: bool = False) -> Optional[date]:
        """
        Converts a raw date string to a datetime.date object.
        If is_end_date is True and raw_date is 'Present' or empty, returns date.today().
        """
        from datetime import datetime, date
        normalized = cls.normalize(raw_date)
        
        if not normalized or normalized == "Unknown":
            return date.today() if is_end_date else None
            
        if normalized == "Present":
            return date.today()
            
        # Try YYYY-MM
        if len(normalized) == 7 and normalized[4] == '-':
            try:
                return datetime.strptime(normalized, "%Y-%m").date()
            except: pass
            
        # Try YYYY
        if len(normalized) == 4 and normalized.isdigit():
            try:
                # If it's an end date and only year is provided, assume end of year? 
                # Or just start of year for consistency. Let's use Jan 1st.
                return date(int(normalized), 1, 1)
            except: pass
            
        return None
