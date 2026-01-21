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
        
        # 1. Scan for dates and categorize lines
        for line in lines:
            if self.DATE_REGEX.search(line):
                dates.append(line)
            else:
                # Potential Role Header?
                # Heuristic: Not a bullet point, not too long, not too short.
                is_bullet = line.startswith(('-', '*', '•', '+'))
                if not is_bullet and 4 < len(line) < 100:
                    if "EDUCATION" not in line.upper() and "EXPERIENCE" not in line.upper():
                        roles.append(line)
                    
        # 2. Reconstruct Experience
        experience = []
        limit = min(len(roles), len(dates))
        
        from cv_formatter.enricher.timeline_analyzer import TimelineAnalyzer
        analyzer = TimelineAnalyzer()
        
        for i in range(limit):
            role_header = roles[i]
            date_line = dates[i]
            
            # Normalize dates for the analyzer
            match = self.DATE_REGEX.search(date_line)
            start_date, end_date = "Unknown", "Unknown"
            if match:
                # Split parts (e.g. "Mar 2023 - Ago 2025")
                parts = re.split(r'[\s\-\u2013]+', match.group(0))
                if len(parts) >= 2:
                    # Crude split to get start/end components
                    # Analyzer will handle the actual parsing
                    start_date = " ".join(parts[:2])
                    end_date = parts[-1] 

            # Try to determine Company vs Title
            parts = re.split(r'[,|@–-]', role_header, 1)
            title = parts[1].strip() if len(parts) > 1 else role_header
            company = parts[0].strip() if len(parts) > 1 else "Unknown"

            experience.append(ExperienceEntry(
                title=title,
                company=company,
                start_date=start_date,
                end_date=end_date,
                description=role_header # Use full line as description/base
            ))
            
        return CVData(
            full_name="Candidate (Recovered)",
            summary="Extracted via Heuristic Fallback (Resilient Mapping)",
            experience=experience
        )
