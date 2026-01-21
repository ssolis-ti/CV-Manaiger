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

class EnrichmentData(BaseModel):
    target_cv_id: str = Field(..., description="UUID of the original CV this analysis belongs to")
    market_signals: TechStack = Field(default_factory=TechStack, description="Technical breakdown")
    coach_feedback: CareerPath = Field(default_factory=CareerPath, description="Strategic advice")
