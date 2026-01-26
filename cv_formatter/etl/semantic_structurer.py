"""
[MODULE: SEMANTIC STRUCTURER - ONE-SHOT v3]
Role: The 'Intelligent Architect'.
Responsibility: Extract strict structure (Experience, Education, Skills) directly from Raw Text using LLM.
Reasoning: Previous A/B approach (classify lines -> group) was too fragile for messy CVs.
Direct structured output (Schematron) is more robust for context understanding.
"""
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import uuid

from cv_formatter.config import config
from cv_formatter.utils.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# SCHEMAS: DIRECT EXTRACTION
# ============================================================================

class ExperienceItem(BaseModel):
    """A single professional experience entry."""
    company: Optional[str] = Field(None, description="Name of the company or organization")
    title: Optional[str] = Field(None, description="Job title or role")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or text)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM, 'Present', or text)")
    location: Optional[str] = Field(None, description="City, Country or 'Remote'")
    description: Optional[str] = Field(None, description="Full text description of the role")
    description_bullets: List[str] = Field(default_factory=list, description="List of responsibilities and achievements")

class EducationItem(BaseModel):
    """A single education entry."""
    institution: Optional[str] = Field(None, description="University, School, or Training Center")
    degree: Optional[str] = Field(None, description="Degree, Diploma, or Certificate name")
    year: Optional[str] = Field(None, description="Year of graduation or period")

class CertificationItem(BaseModel):
    """A single certification."""
    name: Optional[str] = Field(None, description="Name of the certification")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    year: Optional[str] = Field(None, description="Year obtained")

class TechnicalSkills(BaseModel):
    """Categorized skills."""
    hard_skills: List[str] = Field(default_factory=list, description="Technical hard skills, tools, languages")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills, leadership, communication")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")

class ExtractedCV(BaseModel):
    """The full structured CV extracted in one shot."""
    full_name: Optional[str] = Field(None, description="Candidate's full name if detected")
    professional_summary: Optional[str] = Field(None, description="Profile summary or objective")
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    skills: TechnicalSkills = Field(default_factory=TechnicalSkills)

# ============================================================================
# MAIN CLASS
# ============================================================================

class SemanticStructurer:
    """
    One-Shot Semantic Structurer using Strict JSON Schema.
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.API_KEY_STRUCTURE,
            base_url=config.OPENAI_BASE_URL
        )
        self.model = config.MODEL_STRUCTURE
        logger.info(f"SemanticStructurer (One-Shot) initialized with model: {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_structure(self, text: str) -> ExtractedCV:
        """
        Extracts the full CV structure in a single LLM pass.
        This provides context-aware grouping (Company + Title + Dates).
        """
        logger.info(f"[Structure] Extracting entities from {len(text)} chars...")
        start_time = time.time()
        
        system_prompt = """
        ROLE: Expert CV Parser & Data Structurer.
        TASK: Convert the provided Raw CV Text into a strict, high-fidelity JSON structure.
        
        CRITICAL RULES:
        1. EXPERIENCE GROUPING:
           - DETECT COMPANY & TITLE: If a line says "Company, Title" (e.g. "Google, Software Engineer"), you MUST split them.
           - EXTRACT DESCRIPTION: converting all bullet points into the 'description_bullets' list. If there are no bullets, put the text in 'description'. DO NOT OMIT THIS.
           - DATES: If dates appear at the VERY END of the document or in a detached column, you MUST logically map them to the corresponding Experience entry based on sequence/order.
           
        2. SKILL SEGREGATION:
           - "Hard Skills": Technical tools, languages (Python, AWS, Excel), and methodologies.
           - "Soft Skills": Leadership, communication, teamwork traits.
           - "Languages": Spoken languages (English, Spanish, etc).
        
        3. GENERAL:
           - PRESERVE the original language of the text.
           - PRESERVE full descriptions. Do not summarize.
           - If a section is missing, return only what is found.
        """
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this CV:\n\n{text}"}
                ],
                response_format=ExtractedCV,
                temperature=0,
            )
            
            result = completion.choices[0].message.parsed
            elapsed = time.time() - start_time
            
            # Log Extraction Stats
            exp_count = len(result.experience)
            edu_count = len(result.education)
            skill_count = len(result.skills.hard_skills)
            logger.info(f"[Structure] Success in {elapsed:.2f}s | Exp: {exp_count}, Edu: {edu_count}, Skills: {skill_count}")
            
            return result
            
        except Exception as e:
            logger.error(f"[Structure] Extraction failed: {e}")
            # Return empty structure on failure
            return ExtractedCV()
