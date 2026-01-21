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
        self.model = config.MODEL_ENRICH # Now Schematron-8b by default

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=5, max=30))
    def enrich_cv(self, cv_json: dict, cv_id: str) -> EnrichmentData:
        """
        Generates insights based on the already-structured CV data.
        """
        candidate_name = cv_json.get('full_name', 'Unknown')
        logger.info(f"Enriching CV {cv_id} (Candidate: {candidate_name}) using {self.model}...")
        
        # 0. Deterministic Timeline Analysis
        from cv_formatter.formatter.json_formatter import CVData
        from cv_formatter.enricher.timeline_analyzer import TimelineAnalyzer
        
        try:
             cv_obj = CVData(**cv_json)
             timeline_result = TimelineAnalyzer().analyze(cv_obj)
        except Exception as e:
             logger.warning(f"Timeline analysis failed: {e}")
             timeline_result = None

        system_prompt = """
        ### ROL: Coach de Carrera AI
        ### TAREA: Analizar JSON de CV y generar insights (Enriquecimiento).
        
        --- INSTRUCCIÓN CRÍTICA ---
        **OUTPUT EN ESPAÑOL (ES-LATAM).**
        
        --- OBJETIVOS ---
        1. **Market Signals**: Sugerir cargos (Role Fit) y TechStack clave.
        2. **Signals (SWOT)**: Fortalezas, Debilidades y Riesgos.
        3. **Growth**: Potencial de crecimiento (High/Medium/Low).
        4. **CareerPath**: Habilidades faltantes y certificaciones recomendadas.
        
        --- FORMATO ---
        Obedecer JSON Schema `EnrichmentData`. Ser crítico pero constructivo.
        """

        # Prepare payload
        clean_json_str = json.dumps(cv_json, ensure_ascii=False)

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
            
            # Inject Deterministic Analysis
            if timeline_result:
                result.timeline_analysis = timeline_result
            
            return result

        except Exception as e:
            logger.error(f"Enrichment Failed with primary model {self.model}: {e}")
            
            # FALLBACK STRATEGY
            fallback_model = config.MODEL_STRUCTURE
            if fallback_model and fallback_model != self.model:
                logger.info(f"⚠ Rerouting enrichment to Fallback Model: {fallback_model}...")
                try:
                    completion = self.client.beta.chat.completions.parse(
                        model=fallback_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Analyze this CV JSON:\n{clean_json_str}"}
                        ],
                        response_format=EnrichmentData,
                    )
                    result = completion.choices[0].message.parsed
                    result.target_cv_id = cv_id
                    if timeline_result:
                        result.timeline_analysis = timeline_result
                    
                    logger.info("Fallback Enrichment Successful.")
                    return result
                except Exception as fallback_err:
                    logger.error(f"Fallback model also failed: {fallback_err}")
            
            return None
