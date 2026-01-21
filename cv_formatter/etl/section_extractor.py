"""
[MODULE: STRUCTURE ANALYSIS]
Role: The 'Surgeon'.
Responsibility: cut the CV into logical blocks (Experience, Education, Skills) to reduce LLM context load.
Flow: Cleaned Text -> Keyword Heuristics -> Dictionary <SectionName, TextBlock>.
Logic:
- Uses a dictionary of robust keywords (ES/EN) to detect headers.
- 'Heuristic Fallback': If it fails to split cleanly, it returns the whole text as 'raw_content' to be safe.
Warning: This is a Non-AI approach. Creative CVs with unique headers might NOT be split correctly, relying on the LLM to process the bulk 'raw_content'.
"""
import re
from typing import Dict, List
from cv_formatter.utils.logging_config import get_logger

logger = get_logger(__name__)

class SectionExtractor:
    """
    Heuristic-based extractor to identify and split CV sections.
    """
    
    # Common headers in Spanish (and English fallback)
    SECTION_HEADERS = {
        "experience": [r"experiencia", r"experience", r"historial laboral", r"work history"],
        "education": [r"educaci[óo]n", r"education", r"formaci[óo]n", r"academic"],
        "skills": [r"habilidades", r"skills", r"competencias", r"tecnolog[íi]as", r"conocimientos"],
        "projects": [r"proyectos", r"projects"],
        "languages": [r"idiomas", r"languages"],
        "certifications": [r"certificaciones", r"certifications"],
        "contact": [r"contacto", r"contact", r"datos personales"]
    }

    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Splits the CV text into a dictionary of sections based on headers.
        
        [LOGIC FLOW]:
        1. Iterate line by line.
        2. Clean and lower-case each line.
        3. Check against `SECTION_HEADERS` regex patterns.
        4. If match found -> Mark as split point.
        
        [WARNING / LIMITATION]:
        - This is a HEURISTIC method. It is not AI.
        - [False Positive]: A line like "My Experience in Java..." might trigger the "Experience" section 
          if the regex is too loose (e.g. just checking for word existence).
        - [False Negative]: Creative headers ("Proficiency", "Career Arc") will be missed.
        
        Returns:
            Dict[str, str]: Section Name -> Content.
        """
        sections = {}
        # Simple approach: Find all header positions, then slice text
        
        # 1. Identify header positions
        found_headers = []
        lines = text.split('\n')
        
        for idx, line in enumerate(lines):
            clean_line = line.strip().lower()
            # [HEURISTIC]: Header should be short (<= 5 words). 
            # This prevents extracting "Experience" from a long sentence in a paragraph.
            if len(clean_line.split()) > 5:
                continue
                
            for section_key, patterns in self.SECTION_HEADERS.items():
                for pattern in patterns:
                    # [REGEX STRATEGY]: Match exact line OR line ending with colon.
                    # Anchored to start (^) to avoid mid-sentence matches.
                    if re.match(f"^{pattern}:?$", clean_line):
                        found_headers.append((idx, section_key))
                        break
        
        # Sort headers by position
        found_headers.sort(key=lambda x: x[0])
        
        # 2. Slice content
        if not found_headers:
            # Fallback: treat whole text as raw content or unknown
            return {"raw_content": text}
            
        # Capture content before the first header (usually Profile/Header info)
        if found_headers[0][0] > 0:
            header_info = "\n".join(lines[:found_headers[0][0]])
            if header_info.strip():
                sections["header_info"] = header_info.strip()
        
        # Capture content between headers
        for i in range(len(found_headers)):
            start_idx, key = found_headers[i]
            # Content starts after the header line
            start_content_idx = start_idx + 1
            
            if i < len(found_headers) - 1:
                end_content_idx = found_headers[i+1][0]
            else:
                end_content_idx = len(lines)
            
            content = "\n".join(lines[start_content_idx:end_content_idx]).strip()
            # Append if section already exists (e.g. split Experience)
            if key in sections:
                sections[key] += "\n" + content
            else:
                sections[key] = content
                
        return sections

def extract_sections(text: str) -> Dict[str, str]:
    # Convenience function
    return SectionExtractor().extract_sections(text)
