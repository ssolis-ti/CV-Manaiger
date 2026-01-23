"""
[MODULE: DATE PRE-PROCESSOR]
Role: The 'Date Detective'.
Responsibility: Extract dates BEFORE LLM to reduce dependency on AI.

Flow:
    Raw Text -> extract_all_dates() -> {line_num: DateHint}
    
Direction:
    INPUT: Raw CV text (copy-paste from user)
    OUTPUT: Dict mapping line numbers to extracted dates with confidence

Warning: This is a PRE-PROCESSING step. LLM still runs after for semantic analysis.
"""
import re
from typing import Dict, Optional, Literal
from pydantic import BaseModel
from cv_formatter.utils.date_normalizer import DateNormalizer


class DateHint(BaseModel):
    """
    Represents an extracted date range with confidence level.
    Used by frontend to show warnings on low-confidence dates.
    """
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "low"
    raw_line: str = ""  # Original line for user review


class DatePreProcessor:
    """
    Extracts dates from raw text using regex patterns.
    Strategy: Scan each line, detect date patterns, assign confidence.
    
    Confidence Levels:
    - HIGH: Both start and end dates found in standard format
    - MEDIUM: Only one date found, or non-standard format
    - LOW: Partial match or ambiguous pattern
    """
    
    # Pattern: "Enero 2022 - Presente" or "Jan 2020 - Dec 2021"
    FULL_RANGE_PATTERN = re.compile(
        r'([a-zA-ZáéíóúÁÉÍÓÚ]{3,10})\s*(\d{4})\s*[-–—]\s*'
        r'(Present|Presente|Actualidad|Current|Now|[a-zA-ZáéíóúÁÉÍÓÚ]{3,10})\s*(\d{4})?',
        re.IGNORECASE
    )
    
    # Pattern: "2022 - 2024" or "2022 - Present"
    YEAR_RANGE_PATTERN = re.compile(
        r'(\d{4})\s*[-–—]\s*(Present|Presente|Actualidad|Current|Now|\d{4})',
        re.IGNORECASE
    )
    
    # Pattern: Standalone month-year like "Marzo 2019"
    SINGLE_DATE_PATTERN = re.compile(
        r'([a-zA-ZáéíóúÁÉÍÓÚ]{3,10})\s*(\d{4})',
        re.IGNORECASE
    )

    def extract_all_dates(self, text: str) -> Dict[int, DateHint]:
        """
        Main entry point.
        
        Direction: Line-by-line scan -> DateNormalizer -> DateHint
        
        Returns: {line_number: DateHint} for lines with detected dates
        """
        results: Dict[int, DateHint] = {}
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            hint = self._extract_from_line(line)
            if hint.start_date:  # Only include if we found something
                results[line_num] = hint
        
        return results
    
    def _extract_from_line(self, line: str) -> DateHint:
        """
        Attempts to extract dates from a single line.
        
        Strategy (in order of confidence):
        1. Full range pattern (HIGH confidence)
        2. Year range pattern (HIGH confidence)
        3. Single date pattern (MEDIUM confidence)
        4. DateNormalizer fallback (LOW confidence)
        """
        line = line.strip()
        if not line:
            return DateHint(raw_line=line)
        
        # 1. Try full range: "Enero 2022 - Diciembre 2024"
        match = self.FULL_RANGE_PATTERN.search(line)
        if match:
            start = DateNormalizer.normalize(f"{match.group(1)} {match.group(2)}")
            end_part = match.group(3)
            end_year = match.group(4)
            
            if end_year:
                end = DateNormalizer.normalize(f"{end_part} {end_year}")
            else:
                end = DateNormalizer.normalize(end_part)  # "Present"
            
            return DateHint(
                start_date=start,
                end_date=end,
                confidence="high",
                raw_line=line
            )
        
        # 2. Try year range: "2022 - 2024"
        match = self.YEAR_RANGE_PATTERN.search(line)
        if match:
            start = match.group(1)
            end = DateNormalizer.normalize(match.group(2))
            
            return DateHint(
                start_date=start,
                end_date=end,
                confidence="high",
                raw_line=line
            )
        
        # 3. Try single date: "Marzo 2019"
        match = self.SINGLE_DATE_PATTERN.search(line)
        if match:
            date = DateNormalizer.normalize(f"{match.group(1)} {match.group(2)}")
            return DateHint(
                start_date=date,
                end_date=None,
                confidence="medium",
                raw_line=line
            )
        
        # 4. Fallback to DateNormalizer for any year pattern
        if re.search(r'\d{4}', line):
            start, end = DateNormalizer.extract_range(line)
            if start != "Unknown":
                return DateHint(
                    start_date=start,
                    end_date=end if end != "Unknown" else None,
                    confidence="low",
                    raw_line=line
                )
        
        return DateHint(raw_line=line)
