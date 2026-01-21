"""
[MODULE: DATA CONTRACT / SCHEMA]
Role: The 'Rulebook'.
Responsibility: Define strict types for the output using Pydantic.
Flow: LLM JSON Output -> Pydantic Validation -> Safe Dict -> Frontend/API.
Logic:
- Uses Pydantic V2 'BaseModel' for high-performance validation.
- Fields are strongly typed (List[str], Optional[str]) to prevent NullPointerExceptions later.
- 'AnalysisMetadata' section isolates AI inferences (opinion) from facts (Experience/Education).
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

class ExperienceEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal unique ID")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    start_date: Optional[str] = Field(None, description="MUST extract date (start). Format: YYYY-MM or YYYY. If 'Present', use 'Present'.")
    end_date: Optional[str] = Field(None, description="MUST extract date (end). Format: YYYY-MM or YYYY. If 'Present', use 'Present'.")
    description: Optional[str] = Field("", description="Description of the role")
    
    # Hidden tags / analysis
    skills_used: List[str] = Field(default_factory=list, description="Skills inferred from description")
    impact_metrics: List[str] = Field(default_factory=list, description="Quantifiable metrics/impact extracted from description")

    @model_validator(mode='after')
    def check_dates(self):
        """
        Heuristic: If dates are missing, auto-extract from title/description using Regex.
        This provides a fallback for "lazy" LLMs.
        """
        import re
        
        # If dates are already there, do nothing
        if self.start_date:
            return self
            
        # Text to search (Title often contains "Role - Company - 2020-2022")
        search_text = f"{self.title or ''} {self.company or ''} {self.description or ''}"
        
        # Regex for "YYYY - YYYY" or "YYYY - Present"
        # 1. "(20\d{2})[\s\-\u2013]+(Present|Actualidad|Current|Now|20\d{2})"
        year_pattern = re.search(r'(20\d{2})[\s\-\u2013]+(Present|Actualidad|Current|Now|20\d{2})', search_text, re.IGNORECASE)
        
        if year_pattern:
            self.start_date = year_pattern.group(1)
            raw_end = year_pattern.group(2)
            
            if raw_end.lower() in ['present', 'actualidad', 'current', 'now']:
                self.end_date = "Present"
            else:
                self.end_date = raw_end
        
        return self

class EducationEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal unique ID")
    degree: Optional[str] = Field(None, description="Degree or certification name")
    institution: Optional[str] = Field(None, description="University or Institution")
    year: Optional[str] = Field(None, description="Year of graduation or period")

class SkillSection(BaseModel):
    hard_skills: List[str] = Field(default_factory=list, description="Technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills / competencies")

    @model_validator(mode='before')
    @classmethod
    def check_list(cls, v):
        """
        Resilience: If LLM returns a list of strings instead of an object,
        assume they are all hard_skills.
        """
        if isinstance(v, list):
            return {"hard_skills": v, "soft_skills": []}
        return v

class AnalysisMetadata(BaseModel):
    seniority: Optional[str] = Field(None, description="Estimated seniority level (Junior, Mid, Senior, Lead, Executive)")
    writing_style: Optional[str] = Field(None, description="Tone and style of the CV (e.g., Action-oriented, Passive, Academic)")
    llm_summary: Optional[str] = Field(None, description="A short AI-generated critique or summary of the candidate's profile")
    
    # Split Analysis (Risk vs Strength)
    risk_flags: List[str] = Field(default_factory=list, description="Negative indicators (e.g. 'Job Hopper', 'Employment Gaps')")
    strength_signals: List[str] = Field(default_factory=list, description="Positive indicators (e.g. 'Promotion', 'High Impact', 'Prestigous Company')")

class ATSAnalysis(BaseModel):
    score: int = Field(0, description="ATS Compatibility Score (0-100)")
    is_parsable: bool = Field(True, description="Human readable?")
    issues: List[str] = Field(default_factory=list, description="List of ATS-unfriendly elements found (e.g. 'Emojis', 'Columns identified')")
    missing_sections: List[str] = Field(default_factory=list, description="Critical sections not found")

    @model_validator(mode='before')
    @classmethod
    def check_lists(cls, v):
        """
        Resilience: LLM sometimes returns '0' or '1' instead of a list for issues.
        """
        if isinstance(v, dict):
            for field in ['issues', 'missing_sections']:
                val = v.get(field)
                if isinstance(val, int):
                    # If it says "0 issues", convert to empty list
                    v[field] = []
                elif isinstance(val, str):
                     # If it says "None", convert to empty
                     v[field] = [val]
        return v


class CVData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this CV version")
    full_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = Field("", description="Professional summary/profile")
    
    # Metadata / Analysis (New Section)
    metadata: Optional[AnalysisMetadata] = Field(default_factory=AnalysisMetadata, description="AI-inferred analysis of the candidate")
    ats_analysis: Optional[ATSAnalysis] = Field(None, description="Technical ATS check results")
    
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    skills: SkillSection = Field(default_factory=SkillSection)
    languages: List[str] = Field(default_factory=list)
    
    # Excluded from final output if needed, but kept for debugging
    raw_text: Optional[str] = Field(None, description="Original cleaned text, excluded from validation usually")

def format_to_dict(cv_data: CVData) -> dict:
    """
    Safely converts the Pydantic model to a dictionary.
    
    WARNING: This is the Final Contract. 
    Any field not defined in the Schema above will NOT exist in the output.
    """
    return cv_data.model_dump(exclude_none=True)
