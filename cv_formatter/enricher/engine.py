"""
[MODULE: ENRICHMENT ENGINE]
Role: The 'Career Coach'.
Responsibility: Analyze the structured CV data to generate insights and advice.
Flow: Valid JSON (CVData) -> Gemma 3 Analysis -> EnrichmentData.
Logic:
- Uses a separate configuration for the 'Creative' model (Gemma 3).
- Prompts are focused on 'Advisory' and 'Market Fit', not data extraction.
- Fails softly: If Gemma fails to enrich, the main pipeline continues without insights.
"""
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import json

from cv_formatter.config import config
from cv_formatter.enricher.schemas import EnrichmentData
from cv_formatter.utils.logging_config import get_logger

logger = get_logger(__name__)

class EnrichmentService:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.API_KEY_ENRICH,
            base_url=config.OPENAI_BASE_URL
        )
        self.model = config.MODEL_ENRICH # Gamma 3 (or configured secondary model)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    def enrich_cv(self, cv_json: dict, cv_id: str) -> EnrichmentData:
        """
        Generates insights based on the already-structured CV data.
        """
        candidate_name = cv_json.get('full_name', 'Unknown')
        logger.info(f"Enriching CV {cv_id} (Candidate: {candidate_name}) using {self.model}...")
        
        # We send the JSON string to save tokens (no need to re-parse raw text)
        clean_json_str = json.dumps(cv_json, ensure_ascii=False)
        
        system_prompt = """
        You are an expert Technical Recruiter and Career Coach.
        You will receive a CV in JSON format.
        
        --- CRITICAL INSTRUCTION ---
        **OUTPUT MUST BE IN SPANISH (ES-LATAM).**
        
        --- OBJECTIVES ---
        1. **Market Signals**:
           - **TechStack (Dev/Core)**: Languages, Frameworks, Cloud (e.g. Python, React, AWS, Windows Server).
           - **Tools (SaaS/Ops)**: Platforms, Ticket systems, Design tools (e.g. Jira, Slack, Figma, MercadoPublico, SAP).
           - **Role Fit**: Suggest specific job titles (e.g. "Soporte TI N2", "DevOps Junior").
        
        2. **Coach Feedback (CareerPath)**:
           - **Missing Skills**: What is missing for the NEXT level? (e.g. "If Sysadmin, missing Cloud/Azure knowledge").
           - **Certifications**: Suggest specific certs (e.g. "ITIL v4", "AWS Practitioner").
           - **Tips**: Constructive criticism on the CV content (e.g. "Falta cuantificar resultados").
        
        --- OUTPUT ---
        Strictly adhere to the `EnrichmentData` JSON schema.
        Be critical but constructive.
        """

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this CV JSON:\n{clean_json_str}"}
                ],
                response_format=EnrichmentData,
            )
            
            result = completion.choices[0].message.parsed
            # Ensure the ID matches the source
            result.target_cv_id = cv_id
            
            return result

        except Exception as e:
            logger.error(f"Enrichment Failed: {e}")
            # Fail soft: Return None implies "No Insights Available"
            return None
