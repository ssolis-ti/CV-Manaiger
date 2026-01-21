import re
from typing import List, Optional
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry

class HeuristicExtractor:
    """
    Final Tier Extractor: Data Preservation Champion.
    Logic:
    1. Identify Role Headers (non-bullet, specific length).
    2. Collect all text AFTER a Header until the next Header (the 'Chunk').
    3. Identify all Dates in the document.
    4. ZIP Headers+Chunks with Dates sequentially.
    """
    
    DATE_REGEX = re.compile(
        r"((?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}[\s\-\u2013]+(?:Present|Actualidad|Current|Now|\w{3}\s*\d{4}))", 
        re.IGNORECASE
    )
    
    def extract(self, text: str) -> CVData:
        from cv_formatter.utils.date_normalizer import DateNormalizer
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Structure: List of { "header": str, "description": List[str] }
        chunks = []
        lead_in = []
        current_chunk = None
        
        EXCLUDE = ["RESUMEN", "HABILIDADES", "IDIOMAS", "OTROS", "EDUCACIÓN", "CERTIFICACIONES", "COMPETENCIAS"]

        # Phase 1: Chunking with content preservation
        for line in lines:
            # Heuristic for Role Header: Not a bullet, mid-length, not excluded
            is_bullet = line.startswith(('-', '*', '•', '+'))
            is_header = not is_bullet and 6 < len(line) < 110 and not any(x in line.upper() for x in EXCLUDE)
            
            # Additional signal: Does it contain a date?
            has_date = self.DATE_REGEX.search(line) is not None

            if is_header or has_date:
                # If we have a date but line is long, it might be a role with date (Good!)
                # If we have a date and it's a short line, it's a "Footer Date" (Anchor)
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = {"header": line, "description": []}
            else:
                if current_chunk:
                    current_chunk["description"].append(line)
                else:
                    lead_in.append(line)
        
        if current_chunk:
            chunks.append(current_chunk)

        # Phase 2: Proximity-based Date Extraction
        experience = []
        normalized_dates = []
        # Find all dates in doc for global fallback
        all_raw_dates = self.DATE_REGEX.findall(text)
        
        for chunk in chunks:
            header = chunk["header"]
            desc_lines = chunk["description"]
            
            # 1. Check same line (Header)
            start_date, end_date = DateNormalizer.extract_range(header)
            
            # 2. Check next line of description if header had no date
            if start_date == "Unknown" and desc_lines:
                start_date, end_date = DateNormalizer.extract_range(desc_lines[0])
            
            # 3. Clean Header of Date Noise for Title/Company
            clean_header = self.DATE_REGEX.sub("", header).strip()
            
            # Split "Company, Role"
            parts = re.split(r'[,|@–-]', clean_header, 1)
            if len(parts) > 1:
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                company = "Unknown Company"
                title = clean_header

            experience.append(ExperienceEntry(
                title=title or "Position (Recovered)",
                company=company or "Unknown Company",
                start_date=start_date if start_date != "Unknown" else None, 
                end_date=end_date if end_date != "Unknown" else None,
                description="\n".join(desc_lines) if desc_lines else clean_header
            ))
            
        return CVData(
            full_name=lead_in[0] if lead_in else "Candidate (Recovered)",
            summary="\n".join(lead_in[1:4]) if len(lead_in) > 1 else "Extracted via Proximity-Logic Heuristic",
            experience=experience
        )
