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
from typing import List, Optional
from pydantic import BaseModel, Field

class ExperienceEntry(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or string)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM or 'Present')")
    description: str = Field(..., description="Description of the role")
    
    # Hidden tags / analysis
    skills_used: List[str] = Field(default_factory=list, description="Skills inferred from description")
    impact_metrics: List[str] = Field(default_factory=list, description="Quantifiable metrics/impact extracted from description")

class EducationEntry(BaseModel):
    degree: str = Field(..., description="Degree or certification name")
    institution: str = Field(..., description="University or Institution")
    year: Optional[str] = Field(None, description="Year of graduation or period")

class SkillSection(BaseModel):
    hard_skills: List[str] = Field(default_factory=list, description="Technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills / competencies")

class AnalysisMetadata(BaseModel):
    seniority: str = Field(..., description="Estimated seniority level (Junior, Mid, Senior, Lead, Executive)")
    writing_style: str = Field(..., description="Tone and style of the CV (e.g., Action-oriented, Passive, Academic)")
    llm_summary: str = Field(..., description="A short AI-generated critique or summary of the candidate's profile")
    tags_hidden: List[str] = Field(default_factory=list, description="Internal tags for filtering (e.g., 'high_potential', 'job_hopper')")

class CVData(BaseModel):
    full_name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    summary: str = Field("", description="Professional summary/profile")
    
    # Metadata / Analysis (New Section)
    metadata: AnalysisMetadata = Field(..., description="AI-inferred analysis of the candidate")
    
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
