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
        wait=wait_exponential(multiplier=2, min=5, max=15),
        retry=retry_if_exception_type(Exception)
    )
    def tag_cv(self, text: str, language: str = "es") -> CVData:
        """
        Uses OpenAI to analyze the raw (or cleaned) text and extract structured data.
        Includes Retries and Token Logging.
        """
        if not text:
            return CVData(full_name="Unknown", summary="No content provided")

        # [PROMPT STRATEGY]
        # We act as an HR Expert. 
        # Crucial instruction: "Adhere strictly to JSON Schema".
        
        # PROMPT REPOSITORY
        PROMPTS = {
            "es": """
            Eres un asistente experto en RRHH. Tu tarea es extraer información estructurada de un CV.
            
            --- OBJETIVOS ---
            1. **Extracción**: Identifica hechos claros (Fechas, Empresas, Instituciones).
               - **Fechas**: Si ves "2023", úsalo. "Presente"/"Actualidad" es la fecha actual.
               - **ADVERTENCIA**: Las fechas pueden aparecer AL FINAL del bloque de texto. ¡Escanea todo!
               
               --- REGLA NO NEGOCIABLE: FECHAS (CRITICO) ---
               DEBES extraer las fechas de cada experiencia. No las dejes vacías (null).
               Busca formatos como: "Mes/Año - Actualidad", "2018 - 2019".
               Si la fecha está en la línea del título (ej: "Google, 2020-2022"), EXTRAELA.
               
               *** ESTRATEGIA DE COLUMNAS (IMPORTANTE) ***
               Si ves una lista de fechas AL FINAL del texto (ej. "Mar 2023... Ene 2020..."),
               y una lista de roles AL PRINCIPIO, asígnalas SECUENCIALMENTE.
               (1er Rol -> 1ra Fecha, 2do Rol -> 2da Fecha, etc.)
               NO ignores los roles solo porque las fechas están lejos.
               
               --- NON-NEGOTIABLE RULE: SKILLS ---
               The 'skills' field is an OBJECT, not a string or list.
               Structure: { "hard_skills": [...], "soft_skills": [...] }
               
            2. **Análisis Profundo (Metadata)**:
               - **Seniority**: Estima nivel (Junior, Mid, Senior, Lead).
               - **Estilo**: Tono del CV (Conciso, Verboso, Orientado a la acción).
            
            3. **Extracción de PERLAS OCULTAS**:
               - **Hard Skills**: Busca herramientas explícitas.
               - **Impacto**: Busca métricas numéricas.
               
               --- ONE-SHOT EXAMPLE (Ejemplo) ---
               Input: 
               "Gerente de TI | Microsoft
               Responsable de infraestructura global.
               Ene 2020 - Actualidad" 

               Output (JSON):
               {
                 "experience": [
                   {
                     "title": "Gerente de TI",
                     "company": "Microsoft",
                     "start_date": "2020-01",
                     "end_date": "Present",
                     "description": "Responsable de infraestructura global."
                   }
                 ]
               }
            
            --- OUTPUT FORMAT ---
            You MUST adhere strictly to the provided JSON Schema.
            """,
            
            "en": """
            You are an expert HR AI assistant. Your task is to extract structured information from a CV/Resume.
            
            --- OBJECTIVES ---
            1. **Extraction**: Identify clear facts (Dates, Companies, Schools).
               - **Dates**: If only "2023" is present, use it. "Present"/"Current" is today.
               - **WARNING**: Dates might appear at the END of the text block. Scan everything!
               
               --- NON-NEGOTIABLE RULE: DATES (CRITICAL) ---
               You MUST extract dates for every experience entry. Do not leave them null.
               Look for: "Month/Year - Present", "YYYY - YYYY".
               If date is in the header line, EXTRACT IT.
               
               --- NON-NEGOTIABLE RULE: SKILLS ---
               The 'skills' field is an OBJECT. Structure: { "hard_skills": [...], "soft_skills": [...] }
               
            2. **Deep Analysis (Metadata)**:
               - **Seniority**: Estimate level (Junior, Mid, Senior).
               - **Style**: Analyze writing tone.
            
            3. **Hidden Gems**:
               - **Hard Skills**: explicit tools/techs.
               - **Impact**: numeric metrics.
               
               --- ONE-SHOT EXAMPLE ---
               Input: "Project Manager | Microsoft | Jan 2020 - Present"
               Output (JSON): { "experience": [{ "title": "Project Manager", "start_date": "2020-01", "end_date": "Present" }] }
            
            --- OUTPUT FORMAT ---
            You MUST adhere strictly to the provided JSON Schema.
            """
        }
        
        # Select prompt based on detected language (Default to English if unknown, or Spanish if preferred)
        # Using 'es' as default/fallback since this is a Latam-focused tool currently.
        lang_key = language if language in PROMPTS else "es"
        system_prompt = PROMPTS[lang_key]
        
        logger.info(f"Using System Prompt Language: {lang_key}")

        
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

def tag_cv(text: str, language: str = "es") -> CVData:
    tagger = LLMTagger()
    return tagger.tag_cv(text, language)
