"""
[MODULE: ENRICHMENT SCHEMAS]
Role: The 'Twin Contract'.
Responsibility: Define the structure for the 'Insights' JSON (Layer 2).
Flow: EnrichmentService -> Pydantic Validation -> cv_insights.json
Logic:
- Separates 'Market Signals' (Hard data/Stack) from 'Coach Feedback' (Soft suggestions).
- 'target_cv_id' ensures strict linkage to the original CV (Facts).
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class TechStack(BaseModel):
    stack_detected: List[str] = Field(default_factory=list, description="Core technologies detected (e.g. 'Python', 'React', 'AWS')")
    tools_detected: List[str] = Field(default_factory=list, description="Tools and platforms (e.g. 'Jira', 'Docker', 'Kubernetes')")
    role_fit_scenarios: List[str] = Field(default_factory=list, description="Possible job titles this profile fits (e.g. 'Backend Engineer', 'DevOps')")

class CareerPath(BaseModel):
    missing_critical_skills: List[str] = Field(default_factory=list, description="Skills often required for this role level but missing")
    recommended_certifications: List[str] = Field(default_factory=list, description="Industry standard certs that would add value")
    improvement_tips: List[str] = Field(default_factory=list, description="Actionable advice to improve the CV content")

class TimelineAnalysis(BaseModel):
    total_years_experience: Optional[float] = Field(None, description="Calculated years of experience")
    avg_tenure_months: Optional[int] = Field(None, description="Average months per role")
    detected_gaps: List[str] = Field(default_factory=list, description="List of gaps > 6 months (e.g. 'Aug 2018 – Jan 2019')")
    job_hopping_risk: Optional[bool] = Field(None, description="True if average tenure is very low")
    stability_score: Optional[int] = Field(None, description="Stability score 1-10")

class ProfileSignals(BaseModel):
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    weaknesses: List[str] = Field(default_factory=list, description="Key weaknesses or areas for improvement")
    risk_flags: List[str] = Field(default_factory=list, description="Red flags like inconsistent dates or vague descriptions")
    growth_potential: Optional[str] = Field(None, description="High / Medium / Low assessment")

class EnrichmentData(BaseModel):
    target_cv_id: str = Field(..., description="UUID of the original CV this analysis belongs to")
    
    # Quantitative (Deterministic)
    timeline_analysis: Optional[TimelineAnalysis] = Field(None, description="Logic-based temporal analysis")
    
    # Qualitative (LLM)
    market_signals: TechStack = Field(default_factory=TechStack, description="Technical breakdown")
    coach_feedback: CareerPath = Field(default_factory=CareerPath, description="Strategic advice")
    profile_signals: Optional[ProfileSignals] = Field(None, description="SWOT-style analysis")
