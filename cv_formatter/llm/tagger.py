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
        
        # PROMPT REPOSITORY (Optimized for 8B)
        PROMPTS = {
            "es": """
            ### ROL: Experto RRHH AI (Estructuración)
            ### TAREA: Extraer JSON de CV según Schema.
            
            --- REGLAS CRÍTICAS ---
            1. **FECHAS (OBLIGATORIO)**: Extraer 'start_date' y 'end_date'. 
               - Ej: "Mar 2023 - Pres" -> start: "2023-03", end: "Present"
            2. **COLUMNAS**: Si fechas están al final, asignar secuencialmente a cargos arriba.
            3. **SKILLS**: Objeto con {hard_skills: [], soft_skills: []}.
            
            --- EJEMPLO ---
            Input: "Gerente TI | Microsoft | Ene 2020 - Pres"
            Output: {"experience": [{"title": "Gerente TI", "company": "Microsoft", "start_date": "2020-01", "end_date": "Present"}]}
            
            --- FORMATO ---
            Obedecer JSON Schema estrictamente. NO añadir texto extra.
            """,
            
            "en": """
            ### ROLE: AI HR Expert (Structuring)
            ### TASK: Extract JSON from CV per Schema.
            
            --- CRITICAL RULES ---
            1. **DATES (MANDATORY)**: Extract 'start_date' and 'end_date'.
               - e.g. "Jan 2020 - Pres" -> start: "2020-01", end: "Present"
            2. **COLUMNS**: If dates are at the end, assign sequentially to roles above.
            3. **SKILLS**: Object {hard_skills: [], soft_skills: []}.
            
            --- EXAMPLE ---
            Input: "Project Manager | Google | Jan 2018 - Dec 2019"
            Output: {"experience": [{"title": "Project Manager", "company": "Google", "start_date": "2018-01", "end_date": "2019-12"}]}
            
            --- FORMAT ---
            Obey JSON Schema strictly. Output ONLY JSON.
            """
        }
        
        # Select prompt based on detected language (Default to English if unknown, or Spanish if preferred)
        # Using 'es' as default/fallback since this is a Latam-focused tool currently.
        lang_key = language if language in PROMPTS else "es"
        system_prompt = PROMPTS[lang_key]
        
        logger.info(f"Using System Prompt Language: {lang_key}")

        
        # 1. OPTIMIZATION: Count Tokens before sending
        # [FAILSAFE]: Truncate robustly to prevent 400 Bad Request on massive inputs.
        # Assuming ~128k Context Window (Gemma/Schematron). Safety limit: ~100,000 chars.
        MAX_CHARS = 100000
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
