"""
[MODULE: ARTIFICIAL INTELLIGENCE]
Role: The 'Brain'.
Responsibility: Interface with external LLM APIs to interpret text.
Flow: Text -> System Prompt + User Data -> API Call (OpenAI/Inference.net) -> Structured Object.
Logic:
- 'Prompt Engineering': Acts as an HR Expert. 
- 'Resilience': Uses 'tenacity' for retry logic (Backoff) to handle 429/5xx errors.
- 'Observability': Logs token usage and cost per call.
Warning: Latency is dependent on the external API. Cost scales with input size.
"""
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

from cv_formatter.config import config
from cv_formatter.formatter.json_formatter import CVData
from cv_formatter.utils.token_counter import count_tokens, estimate_cost
from cv_formatter.utils.logging_config import get_logger

# Configure simple logger
logger = get_logger(__name__)

class LLMTagger:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.API_KEY_STRUCTURE,
            base_url=config.OPENAI_BASE_URL
        )
        self.model = config.MODEL_STRUCTURE

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def tag_cv(self, text: str) -> CVData:
        """
        Uses OpenAI to analyze the raw (or cleaned) text and extract structured data.
        Includes Retries and Token Logging.
        """
        if not text:
            return CVData(full_name="Unknown", summary="No content provided")

        # [PROMPT STRATEGY]
        # We act as an HR Expert. 
        # Crucial instruction: "Adhere strictly to JSON Schema".
        # This reduces "yapping" (conversational filler) and forces data-only output.
        system_prompt = """
        You are an expert HR AI assistant. Your task is to extract structured information from a CV/Resume.
        
        --- INPUT DATA ---
        You will receive a semi-structured text. 
        It has been processed by an ETL layer to normalize formatting.
        
        --- OBJETIVOS ---
        1. **Extracción**: Identifica hechos claros (Fechas, Empresas, Instituciones).
           - **Smart Parsing**: Si Empresa y Cargo están en la misma línea, sepáralos.
           - **Fechas**: Si ves "2023", úsalo. "Presente"/"Actualidad" es la fecha actual.
           - **ADVERTENCIA**: Las fechas pueden aparecer AL FINAL del bloque de texto. ¡Escanea todo!
           
           --- NON-NEGOTIABLE RULE: DATES (CRITICAL) ---
           You MUST extract dates for every experience entry.
           Do not leave them null. Look for:
           - "YYYY - YYYY"
           - "Month/Year - Present"
           - "Current" / "Actualidad" -> end_date: "Present"
           
           If you see a date range like "2018 - 2020", split it!
           start_date: "2018"
           end_date: "2020"

           If the date is in the header line (e.g. "Google, 2020-2022"), EXTACT IT.
           Do not include the date in the 'company' or 'title' fields. Move it to start_date/end_date.
           
           --- NON-NEGOTIABLE RULE: SKILLS ---
           The 'skills' field is an OBJECT, not a string or list.
           Structure: { "hard_skills": [...], "soft_skills": [...] }

           Any skill explicitly mentioned in the text MUST be added to 'skills.hard_skills'.
           Inferred or generalized skills go ONLY to metadata or enrichment.
        2. **Análisis Profundo (Metadata)**:
           - **Seniority**: Estima nivel (Junior, Mid, Senior, Lead).
           - **Estilo**: Tono del CV (Conciso, Verboso, Orientado a la acción).
           - **Resumen LLM**: Breve resumen interno para reclutadores (ej. "Fuerte en Java pero saltos cortos").
           - **Análisis (Flags)**:
             - **Riesgos**: 'Job Hopping' (muchos puestos cortos), 'Lagunas' (>6 meses).
             - **Fortalezas**: 'Promociones rápidas', 'Empresas Top', 'Liderazgo'.
        3. **Extracción de PERLAS OCULTAS (Crucial)**:
           - **Hard Skills (HECHOS)**: Busca herramientas/tecnologías explícitas (e.g. "Windows", "Python").
             > **REGLA**: Si la palabra está en el texto, DEBE ir a 'skills.hard_skills'. No la guardes para análisis.
           - **Impacto**: Busca números (%, $, aumento, reducción) -> 'impact_metrics'.
           - **Soft Skills**: Palabras clave de comunicación/liderazgo -> 'skills.soft_skills'.
           
           --- ONE-SHOT EXAMPLE (Ejemplo) ---
           Input:
           "Gerente de Proyectos | Microsoft
           Ene 2020 - Actualidad
           Liderazgo de equipos."

           Output (JSON):
           {
             "experience": [
               {
                 "title": "Gerente de Proyectos",
                 "company": "Microsoft",
                 "start_date": "2020-01",
                 "end_date": "Present",
                 "description": "Liderazgo de equipos."
               }
             ]
           }

        --- OUTPUT FORMAT ---
        You MUST adhere strictly to the provided JSON Schema.
        If a field is ambiguous, prefer null. Do not hallucinate data not present in text.
        """
        
        # 1. OPTIMIZATION: Count Tokens before sending
        # [FAILSAFE]: Truncate robustly to prevent 400 Bad Request on massive inputs.
        # Assuming ~8k Context Window. Safety limit: ~32,000 chars.
        MAX_CHARS = 32000
        if len(text) > MAX_CHARS:
            logger.warning(f"Input text too long ({len(text)} chars). Truncating to {MAX_CHARS} chars to save context.")
            text = text[:MAX_CHARS] + "\n...[TRUNCATED_BY_SYSTEM]..."
        
        input_tokens_est = count_tokens(system_prompt + text, self.model)
        logger.info(f"Preparing to send ~{input_tokens_est} input tokens to {self.model}")

        try:
            # CALL TO OPENAI
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the CV Text:\n\n{text}"}
                ],
                response_format=CVData,
                temperature=0,
            )
            
            result = completion.choices[0].message.parsed
            
            # 2. OPTIMIZATION: Log Usage for Cost Analysis
            usage = completion.usage
            if usage:
                cost = estimate_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
                logger.info(f"OpenAI Usage: {usage.total_tokens} tokens (In: {usage.prompt_tokens}, Out: {usage.completion_tokens}). Est. Cost: ${cost:.6f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling OpenAI after retries: {e}")
            # Raise so Facade can handle it or let it crash depending on policy
            raise e

def tag_cv(text: str) -> CVData:
    tagger = LLMTagger()
    return tagger.tag_cv(text)
