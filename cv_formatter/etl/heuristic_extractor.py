import re
from typing import List, Optional
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry

class HeuristicExtractor:
    """
    Last-resort extractor that prioritizes DATA PRESERVATION over perfect structure.
    Logic:
    1. Identify 'Date Anchors' (e.g., 'Mar 2023 - Pres').
    2. Collect ALL lines between two anchors.
    3. Map anchors to roles sequentially.
    """
    
    DATE_REGEX = re.compile(
        r"((?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}[\s\-\u2013]+(?:Present|Actualidad|Current|Now|\w{3}\s*\d{4}))", 
        re.IGNORECASE
    )
    
    def extract(self, text: str) -> CVData:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Structure: List of { "date": str, "content": List[str] }
        blocks = []
        current_content = []
        current_date = "Unknown Date"
        
        # Capture lead-in text (e.g. name, professional summary)
        lead_in = []
        first_date_found = False

        for line in lines:
            date_match = self.DATE_REGEX.search(line)
            if date_match:
                # If we were already collecting a block, save it
                if first_date_found:
                    blocks.append({"date": current_date, "lines": current_content})
                
                first_date_found = True
                current_date = date_match.group(0)
                current_content = [] # Reset for next block
                # We also keep the line itself in content if it has more text
                remaining_text = line.replace(current_date, "").strip()
                if remaining_text:
                    current_content.append(remaining_text)
            else:
                if not first_date_found:
                    lead_in.append(line)
                else:
                    current_content.append(line)
        
        # Add the final block
        if first_date_found:
            blocks.append({"date": current_date, "lines": current_content})
        
        experience = []
        for block in blocks:
            raw_lines = block["lines"]
            date_str = block["date"]
            
            # Heuristic for Title: First non-bullet line of the block
            title = "Position (Recovered)"
            description_lines = []
            
            found_title = False
            for l in raw_lines:
                if not found_title and not l.startswith(('-', '*', '•', '+')) and len(l) > 3:
                    title = l
                    found_title = True
                else:
                    description_lines.append(l)
            
            # Normalize dates for analyzer
            parts = re.split(r'[\s\-\u2013]+', date_str)
            start_date = " ".join(parts[:2]) if len(parts) >= 2 else date_str
            end_date = parts[-1] if len(parts) >= 2 else "Present"

            experience.append(ExperienceEntry(
                title=title,
                company="Multiple/Internal", # Heuristic can't easily split company
                start_date=start_date,
                end_date=end_date,
                description="\n".join(description_lines) if description_lines else title
            ))
            
        return CVData(
            full_name=lead_in[0] if lead_in else "Candidate (Recovered)",
            summary="\n".join(lead_in[1:3]) if len(lead_in) > 1 else "Extracted via Resilient Heuristic",
            experience=experience
        )
