from openai import OpenAI
from cv_formatter.config import config
from cv_formatter.formatter.json_formatter import CVData

class LLMTagger:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

    def tag_cv(self, text: str) -> CVData:
        """
        Uses OpenAI to analyze the raw (or cleaned) text and extract structured data.
        """
        if not text:
            # Return empty structure if no text
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

        try:
            # CALL TO OPENAI
            # We use 'response_format' with Pydantic to guarantee valid JSON.
            # This is the Core of the "LLM Friendly" strategy.
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the CV Text:\n\n{text}"}
                ],
                response_format=CVData,
            )
            
            result = completion.choices[0].message.parsed
            return result
            
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            # Return a partial/empty object to avoid crash, or re-raise
            return CVData(full_name="Error Parsing", summary=f"Failed to process CV: {str(e)}")

def tag_cv(text: str) -> CVData:
    tagger = LLMTagger()
    return tagger.tag_cv(text)
