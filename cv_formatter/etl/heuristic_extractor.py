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
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Phase 1: Identify all dates and Role Candidates
        dates = []
        chunks = [] # List of { "header": str, "description": List[str] }
        lead_in = []
        
        current_chunk = None
        
        # Exclusion keywords to avoid picking Resumen/Skills as a role
        EXCLUDE = ["RESUMEN", "HABILIDADES", "IDIOMAS", "OTROS", "EDUCACIÓN", "CERTIFICACIONES", "COMPETENCIAS"]

        for line in lines:
            # 1. Is it a date?
            if self.DATE_REGEX.search(line):
                dates.append(line)
                continue
            
            # 2. Is it a potential Role Header?
            # Heuristic: Not a bullet, reasonable length, not in exclude list
            is_bullet = line.startswith(('-', '*', '•', '+'))
            is_header = not is_bullet and 5 < len(line) < 120 and not any(x in line.upper() for x in EXCLUDE)
            
            if is_header:
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
            
        # Phase 3: Zipping with Footer Dates
        # We assume the user's rule: Roles appear first, Dates appear later/Footer.
        # We zip them by index.
        experience = []
        limit = min(len(chunks), len(dates))
        
        for i in range(limit):
            chunk = chunks[i]
            date_str = dates[i]
            
            header = chunk["header"]
            desc = "\n".join(chunk["description"])
            
            # Robust split for "Company, Role" or "Company | Role" or "Company - Role"
            # We try common separators
            parts = re.split(r'[,|@–-]', header, 1)
            if len(parts) > 1:
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                company = "Unknown Company"
                title = header.strip()

            experience.append(ExperienceEntry(
                title=title or "Position (Recovered)",
                company=company or "Unknown Company",
                start_date=date_str, 
                end_date="Check Timeline",
                description=desc if desc else header
            ))
            
        return CVData(
            full_name=lead_in[0] if lead_in else "Candidate (Recovered)",
            summary="\n".join(lead_in[1:4]) if len(lead_in) > 1 else "Extracted via Resilient Chunking",
            experience=experience
        )
