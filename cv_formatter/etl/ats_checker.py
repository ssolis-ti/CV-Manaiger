"""
[MODULE: ATS CHECKER]
Role: The 'Inspector'.
Responsibility: Audit text for elements that break Applicant Tracking Systems (ATS).
Flow: Raw Text -> Analysis -> Report.
Logic:
- Emoji Detection: ATS hates emojis. We count and flag them.
- Special Character Density: Too many non-ascii symbols?
- Section Headers: Does it follow standard naming?
"""
import re
import emoji
from typing import List, Tuple
from cv_formatter.formatter.json_formatter import ATSAnalysis

class ATSChecker:
    
    def check(self, text: str) -> ATSAnalysis:
        issues = []
        score = 100
        
        # 1. Emoji Check
        emoji_count = emoji.emoji_count(text)
        if emoji_count > 0:
            issues.append(f"Found {emoji_count} emojis/icons. ATS systems cannot read these.")
            score -= (emoji_count * 2) # Penalize 2 points per emoji
            
        # 2. Bullet Point Diversity (Weird symbols)
        # Using regex to find non-standard bullets
        weird_bullets = re.findall(r'[➤➢➔➜⇒►●■◆▪▫]', text)
        if len(weird_bullets) > 5:
            issues.append("Excessive use of non-standard bullet points (e.g. ➤, ■). Use standard dash '-' or dot '•'.")
            score -= 10
            
        # 3. Missing Critical Headers
        text_lower = text.lower()
        required_sections = ["experi", "educ", "skill", "habilid"]
        missing_sections = []
        
        # Check essentially for "Experience" OR "Experiencia" etc.
        # This is a bit redundant with Triage, but this is for 'quality' scoring
        has_exp = any(x in text_lower for x in ["experiencia", "experience", "historial", "career", "trayectoria"])
        if not has_exp:
            missing_sections.append("Experience/Experience")
            score -= 20
            
        has_edu = any(x in text_lower for x in ["educaci", "education", "formacion", "académic", "academic"])
        if not has_edu:
            missing_sections.append("Education/Educación")
            score -= 10
            
        has_skills = any(x in text_lower for x in ["skill", "habilidad", "competencia", "tecnolog", "stack"])
        if not has_skills:
            missing_sections.append("Skills/Habilidades")
            score -= 10

        # Cap score at 0
        if score < 0:
            score = 0
            
        return ATSAnalysis(
            score=score,
            is_parsable=score > 40,
            issues=issues,
            missing_sections=missing_sections
        )
