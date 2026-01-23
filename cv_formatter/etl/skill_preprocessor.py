"""
[MODULE: SKILL PRE-PROCESSOR]
Role: The 'Skill Detective'.
Responsibility: Extract skills BEFORE LLM to ensure no skills are missed.

Flow:
    Raw Text -> extract_skills() -> List[str]
    
Direction:
    INPUT: Raw CV text (copy-paste from user)
    OUTPUT: List of detected hard skills

Warning: This is a PRE-PROCESSING step. Uses regex pattern matching.
"""
import re
from typing import List, Set


class SkillPreProcessor:
    """
    Extracts technical skills from raw text using keyword matching.
    
    Strategy:
    1. Look for "Skills" section in text
    2. Extract comma/bullet separated items
    3. Also scan full text for known tech keywords
    """
    
    # Common tech skills (expandable)
    KNOWN_SKILLS = {
        # Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust', 'php', 'swift', 'kotlin',
        # Frameworks
        'django', 'flask', 'fastapi', 'react', 'angular', 'vue', 'node', 'nodejs', 'express', 'spring', 'laravel',
        # Cloud/DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'jenkins', 'ci/cd', 'gitlab', 'github',
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'oracle',
        # Tools
        'git', 'linux', 'bash', 'jira', 'confluence', 'slack', 'figma', 'postman',
        # AI/ML
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'machine learning', 'ml', 'ai',
        # Web
        'html', 'css', 'sass', 'rest', 'api', 'graphql', 'microservices', 'websocket'
    }
    
    # Section headers that indicate skills
    SKILL_SECTION_PATTERN = re.compile(
        r'(skills|habilidades|competencias|tecnolog[íi]as|technical\s*skills|tech\s*stack)',
        re.IGNORECASE
    )

    def extract_skills(self, text: str) -> List[str]:
        """
        Main entry point.
        
        Strategy:
        1. Find skills section and extract items
        2. Fallback: scan full text for known keywords
        
        Returns: List of unique skill names
        """
        found_skills: Set[str] = set()
        
        # 1. Try to find dedicated skills section
        section_skills = self._extract_from_section(text)
        found_skills.update(section_skills)
        
        # 2. Also scan full text for known keywords (catches skills in descriptions)
        keyword_skills = self._extract_by_keywords(text)
        found_skills.update(keyword_skills)
        
        # Return sorted list for consistency
        return sorted(list(found_skills))
    
    def _extract_from_section(self, text: str) -> Set[str]:
        """
        Finds skills section and extracts comma/bullet separated items.
        """
        skills: Set[str] = set()
        lines = text.split('\n')
        
        in_skills_section = False
        for i, line in enumerate(lines):
            # Check if this line is a skills header
            if self.SKILL_SECTION_PATTERN.search(line):
                in_skills_section = True
                continue
            
            # If in skills section, extract items until next section
            if in_skills_section:
                # Stop at empty line or next section header
                if not line.strip() or (len(line.strip()) < 30 and line.strip().endswith(':')):
                    in_skills_section = False
                    continue
                
                # Split by common separators
                items = re.split(r'[,;|•\-\n]+', line)
                for item in items:
                    clean_item = item.strip().lower()
                    if clean_item and len(clean_item) > 1:
                        # Capitalize properly for display
                        skills.add(item.strip())
        
        return skills
    
    def _extract_by_keywords(self, text: str) -> Set[str]:
        """
        Scans full text for known skill keywords.
        """
        skills: Set[str] = set()
        text_lower = text.lower()
        
        for skill in self.KNOWN_SKILLS:
            # Use word boundary matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Return with proper capitalization
                skills.add(skill.title() if len(skill) > 2 else skill.upper())
        
        return skills
