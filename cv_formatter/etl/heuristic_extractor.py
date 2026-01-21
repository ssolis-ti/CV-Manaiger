import re
from typing import List, Optional
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry

class HeuristicExtractor:
    """
    Last-resort extractor when LLM fails (returns empty or API error).
    Logic:
    1. Identify Date Lines (e.g., "Mar 2023 - Present").
    2. Identify Text Blocks that are likely Roles.
    3. Zip them together sequentially.
    """
    
    DATE_REGEX = re.compile(r"((?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}[\s\-\u2013]+(?:Present|Actualidad|Current|Now|\w{3}\s*\d{4}))", re.IGNORECASE)
    
    def extract(self, text: str) -> CVData:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        roles = []
        dates = []
        
        # 1. Scan for dates
        for line in lines:
            if self.DATE_REGEX.search(line):
                dates.append(line)
            else:
                # Potential Role/Desc line
                # Filter out garbage
                if len(line) > 3 and "EDUCATION" not in line and "EXPERIENCE" not in line:
                    roles.append(line)
                    
        # 2. Try to reconstruct Experience
        experience = []
        
        # Heuristic: If we have N dates, assume the first N role-blocks correspond to them?
        # This is risky. Better approach:
        # The user's CV has distinct blocks: "Company, Role".
        # Let's try to act smart.
        
        # Mapping Strategy: Zip Longest-Blocks with Dates?
        # Fallback Strategy: Just dump text into description and let user fix it, 
        # but attach the Date so score isn't 0.
        
        limit = min(len(roles), len(dates))
        for i in range(limit):
            # Assume role is the first line of the block? 
            # In the user's case, roles are separated by description...
            # This 'roles' list is actually ALL prose.
            # We can't easily distinguish Title from Description without LLM.
            
            # Simplified: Create Generic entries for the dates found.
            # "Role detected via Heuristic"
            
            date_str = dates[i]
            match = self.DATE_REGEX.search(date_str)
            start, end = "Unknown", "Unknown"
            if match:
                parts = re.split(r'[\s\-\u2013]+', match.group(0))
                if len(parts) >= 2:
                    start = parts[0] + " " + parts[1] # "Mar 2023"
                    end = parts[-1] # "Present" or "2025"
            
            # Try to grab a chunk of text as description
            # This is rough, but better than nothing.
            desc_chunk = roles[i] if i < len(roles) else ""
            
            experience.append(ExperienceEntry(
                title="Position (Recovered)",
                company="Unknown",
                start_date=start,
                end_date=end,
                description=desc_chunk
            ))
            
        return CVData(
            full_name="Candidate (Recovered)",
            summary="Extracted via Heuristic Fallback due to AI Service Failure",
            experience=experience
        )
