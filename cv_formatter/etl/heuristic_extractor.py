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
    
    # Unified Date Pattern (Sync with DateNormalizer)
    DATE_REGEX = re.compile(r'(\d{4}|Present|Actualidad|Current|Now|Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', re.IGNORECASE)

    def extract(self, text: str) -> CVData:
        from cv_formatter.utils.date_normalizer import DateNormalizer
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        chunks = []
        lead_in = []
        current_chunk = None
        
        # Expanded exclusions to avoid picking Section Headers as Job Titles
        EXCLUDE = [
            "RESUMEN", "HABILIDADES", "IDIOMAS", "OTROS", "EDUCACIÓN", 
            "CERTIFICACIONES", "COMPETENCIAS", "ESTUDIOS", "EXPERIENCIA", 
            "EXPERIENCE", "EDUCATION", "SKILLS", "CONTACTO", "CONTACT"
        ]

        # Phase 1: Robust Chunking
        for line in lines:
            is_bullet = line.startswith(('-', '*', '•', '+', '➢', '✓'))
            # A line is a header if it's NOT a bullet, is relatively short, and is NOT in EXCLUDE
            is_header_candidate = not is_bullet and 3 < len(line) < 100 and not any(x in line.upper() for x in EXCLUDE)
            
            # Additional signal: Dates make a header candidate much more likely to be a REAL header
            # HOWEVER, a line that is ONLY a date is NOT a header (it's a property of a header)
            has_date = self.DATE_REGEX.search(line) is not None
            is_only_date = has_date and len(re.sub(r'[\d\s\-\u2013\u2014\/\|apresentactualidadcurrntnowEneFebMarAbrMayJunJulAgoSepOctNovDicJanFebMarAprMayJunJulAugSepOctNovDec\(\)\.]', '', line, flags=re.IGNORECASE)) < 3

            # CRITICAL: We only split on candidates that look like structural headers
            # AND are NOT just standalone dates.
            if is_header_candidate and not is_only_date:
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

        # Phase 2: Extraction with Zero-Loss
        experience = []
        for chunk in chunks:
            header = chunk["header"]
            desc_lines = chunk["description"]
            
            # 1. Extract Dates
            start_date, end_date = DateNormalizer.extract_range(header)
            
            # Fallback to first line of description if header has no date
            if start_date == "Unknown" and desc_lines:
                start_date_desc, end_date_desc = DateNormalizer.extract_range(desc_lines[0])
                if start_date_desc != "Unknown":
                    start_date, end_date = start_date_desc, end_date_desc
            
            # 2. Cleanup Title: ONLY clean if we actually found dates to swap them out
            clean_header = header
            if start_date != "Unknown":
                # Conservative removal of 4-digit years only to avoid deleting title words
                clean_header = re.sub(r'\b(20\d{2}|19\d{2}|Present|Actualidad|Current|Now)\b', '', header, flags=re.IGNORECASE).strip()
            
            # 3. Split Title/Company - If no clear separator, use the whole line as Title
            parts = re.split(r'[,|@]', clean_header, 1)
            if len(parts) > 1:
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                company = "Company"
                title = clean_header

            experience.append(ExperienceEntry(
                title=title or clean_header,
                company=company,
                start_date=start_date if start_date != "Unknown" else None, 
                end_date=end_date if end_date != "Unknown" else None,
                description="\n".join(desc_lines) if desc_lines else clean_header
            ))
            
        return CVData(
            full_name=lead_in[0] if lead_in else "Candidate",
            summary="\n".join(lead_in) if lead_in else "",
            experience=experience
        )
