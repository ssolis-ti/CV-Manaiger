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
    """
    Represents a single work experience entry.
    
    Flow: LLM extracts -> Pydantic validates -> Frontend displays
    Redirection: If LLM fails dates, check_dates() validator tries regex fallback
    
    Warning: date_confidence affects frontend UI - "low" shows warning icon
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal unique ID")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    start_date: Optional[str] = Field(None, description="MUST extract date (start). Format: YYYY-MM or YYYY. If 'Present', use 'Present'.")
    end_date: Optional[str] = Field(None, description="MUST extract date (end). Format: YYYY-MM or YYYY. If 'Present', use 'Present'.")
    description: Optional[str] = Field("", description="Description of the role")
    
    # Hidden tags / analysis
    skills_used: List[str] = Field(default_factory=list, description="Skills inferred from description")
    impact_metrics: List[str] = Field(default_factory=list, description="Quantifiable metrics/impact extracted from description")
    
    # --- MANUAL ADJUSTMENT SUPPORT (Frontend Integration) ---
    # Direction: Backend sets confidence -> Frontend shows UI accordingly
    date_confidence: str = Field("high", description="Confidence level: high, medium, low, manual")
    user_adjusted: bool = Field(False, description="True if user manually corrected dates")
    original_date_line: Optional[str] = Field(None, description="Raw text line for user reference")

    @model_validator(mode='after')
    def check_dates(self):
        """
        FALLBACK VALIDATOR: If LLM didn't extract dates, try regex.
        
        Flow: 
            1. Check if dates exist -> return early
            2. Use DateNormalizer to extract from title/company/description
            3. Mark confidence as "medium" if auto-extracted
        
        Warning: This is a last-resort fallback. Pre-processor should handle most cases.
        """
        # If user already adjusted or dates exist, skip
        if self.user_adjusted or self.start_date:
            return self
        
        # Use DateNormalizer for comprehensive extraction
        from cv_formatter.utils.date_normalizer import DateNormalizer
        search_text = f"{self.title or ''} {self.company or ''} {self.description or ''}"
        
        start, end = DateNormalizer.extract_range(search_text)
        if start != "Unknown":
            self.start_date = start
            self.end_date = end if end != "Unknown" else None
            self.date_confidence = "medium"  # Auto-extracted via fallback
        
        return self

class EducationEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Internal unique ID")
    degree: Optional[str] = Field(None, description="Degree or certification name")
    institution: Optional[str] = Field(None, description="University or Institution")
    year: Optional[str] = Field(None, description="Year of graduation or period")

class CertificationEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Name of certification")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    year: Optional[str] = Field(None, description="Year obtained")

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
    """
    ATS compatibility analysis results.
    
    Warning: LLM sometimes returns score as float (0.95) instead of int (95).
    The check_types validator handles this conversion.
    """
    score: int = Field(0, description="ATS Compatibility Score (0-100)")
    is_parsable: bool = Field(True, description="Human readable?")
    issues: List[str] = Field(default_factory=list, description="List of ATS-unfriendly elements found (e.g. 'Emojis', 'Columns identified')")
    missing_sections: List[str] = Field(default_factory=list, description="Critical sections not found")

    @model_validator(mode='before')
    @classmethod
    def check_types(cls, v):
        """
        Resilience validator for LLM output inconsistencies.
        
        Fixes:
        1. score: float (0.95) → int (95)
        2. issues: int/str → list
        """
        if isinstance(v, dict):
            # Fix 1: Convert float score to int
            score = v.get('score')
            if isinstance(score, float):
                # 0.95 → 95, or 85.5 → 85
                v['score'] = int(score * 100) if score <= 1 else int(score)
            
            # Fix 2: Ensure lists are lists
            for field in ['issues', 'missing_sections']:
                val = v.get(field)
                if isinstance(val, int):
                    v[field] = []
                elif isinstance(val, str):
                    v[field] = [val] if val else []
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
    certifications: List[CertificationEntry] = Field(default_factory=list, description="List of certifications")
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
