"""
[MODULE: TRIAGE / GATEKEEPER]
Role: The 'Bouncer'.
Responsibility: Filter out garbage before it hits the expensive LLM.
Flow: Raw Text -> Triage -> (Accepted/Rejected) + Metadata.
Logic:
- Language Detection: Uses 'langdetect' to ensure valid processing.
- Type Classification: Heuristic check (Keywords) to confirm it's a CV.
- Fast Meta: Regex for Email/Name to allow indexing without full parse.
"""

import re
from langdetect import detect, LangDetectException
from typing import Dict, Tuple

class TriageDaemon:
    # Heuristics for CV validation
    # Mixed English/Spanish keywords
    REQUIRED_KEYWORDS = [
        "experiencia", "educación", "education", "experience", 
        "skills", "habilidades", "resumé", "curriculum", "cv", 
        "perfil", "profile", "laboral", "professional", "academy"
    ]
    MIN_KEYWORDS_MATCH = 2
    
    def classify_document(self, text: str) -> bool:
        """
        Determines if the text is likely a CV.
        Strategy: Count occurrence of standard CV sections/keywords.
        Returns: True if it looks like a CV.
        """
        if not text or len(text) < 50:
            return False
            
        text_lower = text.lower()
        matches = sum(1 for kw in self.REQUIRED_KEYWORDS if kw in text_lower)
        
        return matches >= self.MIN_KEYWORDS_MATCH

    def detect_language(self, text: str) -> str:
        """
        Returns 'es', 'en', etc. or 'unknown'.
        """
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    def fast_extract_meta(self, text: str) -> Dict[str, str]:
        """
        Quick regex-based extraction for indexing.
        """
        meta = {"email": None, "name_candidate": None}
        
        # EMAIL REGEX
        # Basic regex for email extraction
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            meta["email"] = email_match.group(0)
            
        # NAME HEURISTIC
        # Usually the first non-empty line, or the first line with Capitalized words.
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # Take the first line as candidate name, assuming it's short
            first_line = lines[0]
            if len(first_line.split()) < 6: # Names shouldn't be full sentences
                meta["name_candidate"] = first_line
        
        # Heuristic fix: If first line is generic (e.g. "Curriculum Vitae"), take the next line
        if meta["name_candidate"]:
            generic_titles = ["curriculum vitae", "resume", "cv", "hoja de vida", "curriculum"]
            if meta["name_candidate"].lower().replace(".", "") in generic_titles:
                 if len(lines) > 1:
                     next_line = lines[1]
                     if len(next_line.split()) < 6:
                        meta["name_candidate"] = next_line
                 else:
                     meta["name_candidate"] = "Unknown"
                 
        return meta

    def triage(self, text: str) -> Tuple[bool, str, Dict]:
        """
        Main entry point.
        Returns: (is_valid, reason, fast_meta)
        """
        context = {}
        
        # 1. Classify
        if not self.classify_document(text):
            return False, "REJECTED: Not a CV (Keywords missing)", {}
            
        # 2. Language
        lang = self.detect_language(text)
        context['language'] = lang
        # For now, we flag it but don't reject purely on language (unless user demands it later)
             
        # 3. Meta
        meta = self.fast_extract_meta(text)
        context.update(meta)
        
        return True, "ACCEPTED", context
