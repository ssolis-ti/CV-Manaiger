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

class ExperienceEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal unique ID")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or string)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM or 'Present')")
    description: Optional[str] = Field("", description="Description of the role")
    
    # Hidden tags / analysis
    skills_used: List[str] = Field(default_factory=list, description="Skills inferred from description")
    impact_metrics: List[str] = Field(default_factory=list, description="Quantifiable metrics/impact extracted from description")

class EducationEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal unique ID")
    degree: Optional[str] = Field(None, description="Degree or certification name")
    institution: Optional[str] = Field(None, description="University or Institution")
    year: Optional[str] = Field(None, description="Year of graduation or period")

class SkillSection(BaseModel):
    hard_skills: List[str] = Field(default_factory=list, description="Technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills / competencies")

class AnalysisMetadata(BaseModel):
    seniority: Optional[str] = Field(None, description="Estimated seniority level (Junior, Mid, Senior, Lead, Executive)")
    writing_style: Optional[str] = Field(None, description="Tone and style of the CV (e.g., Action-oriented, Passive, Academic)")
    llm_summary: Optional[str] = Field(None, description="A short AI-generated critique or summary of the candidate's profile")
    
    # Split Analysis (Risk vs Strength)
    risk_flags: List[str] = Field(default_factory=list, description="Negative indicators (e.g. 'Job Hopper', 'Employment Gaps')")
    strength_signals: List[str] = Field(default_factory=list, description="Positive indicators (e.g. 'Promotion', 'High Impact', 'Prestigous Company')")

class CVData(BaseModel):
    full_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = Field("", description="Professional summary/profile")
    
    # Metadata / Analysis (New Section)
    metadata: Optional[AnalysisMetadata] = Field(default_factory=AnalysisMetadata, description="AI-inferred analysis of the candidate")
    
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
