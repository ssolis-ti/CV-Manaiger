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
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL
        )
        self.model = config.MODEL_ENRICH # Gamma 3 (or configured secondary model)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    def enrich_cv(self, cv_json: dict, cv_id: str) -> EnrichmentData:
        """
        Generates insights based on the already-structured CV data.
        """
        logger.info(f"Enriching CV {cv_id} using {self.model}...")
        
        # We send the JSON string to save tokens (no need to re-parse raw text)
        clean_json_str = json.dumps(cv_json, ensure_ascii=False)
        
        system_prompt = """
        You are an expert Technical Recruiter and Career Coach.
        You will receive a CV in JSON format. Your goal is NOT to extracting basics, but to providing DEEP INSIGHTS.
        
        --- OBJECTIVES ---
        1. **Market Signals (TechStack)**:
           - Scan the entire JSON for tools, languages, and frameworks.
           - Infer the 'Role Fit' (e.g. "Senior Backend Dev", "Data Engineer").
        
        2. **Coach Feedback (CareerPath)**:
           - Identify **Missing Critical Skills** based on the inferred role (e.g. "If DevOps, where is Kubernetes?").
           - Suggest **Certifications** that would boost this specific profile.
           - Provide **Improvement Tips**: Critique the description quality (vague vs quantifiable).
        
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
