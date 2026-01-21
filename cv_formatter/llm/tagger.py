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
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

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

        system_prompt = """
        You are an expert HR AI assistant. Your task is to extract structured information from a CV/Resume.
        
        --- INPUT DATA ---
        You will receive a semi-structured text. 
        It has been processed by an ETL layer to normalize formatting.
        
        --- OBJECTIVES ---
        1. **Extraction**: Identify clear facts (Dates, Companies, Schools).
        2. **Inference (Tagging)**:
           - Look at 'Description' fields. Infer **Hard Skills** used in that specific role.
           - Quantify **Impact**: Look for numbers (%, $, increase, reduction) and extract them as 'impact_metrics'.
           - Classify global skills into Hard vs Soft.
           
        --- OUTPUT FORMAT ---
        You MUST adhere strictly to the provided JSON Schema.
        If a field is ambiguous, prefer null. Do not hallucinate data not present in text.
        """
        
        # 1. OPTIMIZATION: Count Tokens before sending
        # This helps in preventing Context Window errors.
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
