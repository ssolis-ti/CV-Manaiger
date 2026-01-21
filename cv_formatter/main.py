from cv_formatter.etl.cleaner import clean_text
from cv_formatter.etl.section_extractor import extract_sections
from cv_formatter.llm.tagger import tag_cv
from cv_formatter.formatter.json_formatter import format_to_dict
import json

class CVProcessor:
    """
    Facade to process a CV from raw text to structured JSON.
    """
    
    def process_cv(self, raw_text: str) -> dict:
        """
        Main entry point (Facade Method).
        
        Orchestrates the pipeline from Raw Text -> Final JSON.
        
        Data Flow:
        1. [Input] Raw unstructured string.
        2. [ETL Layer] Text is normalized (cleaner.py).
        3. [ETL Layer] Sections are heuristically extracted (section_extractor.py) to provide structure.
        4. [LLM Layer] Structured context is sent to OpenAI to extract intelligence (tagger.py).
        5. [Output Layer] Pydantic model is dumped to a clean Dict (json_formatter.py).
        
        Args:
            raw_text (str): The dirty text pasted by the user.
            
        Returns:
            dict: The final, polished, IA-ready JSON.
        """
        # ---------------------------------------------------------
        # STEP 1: ETL - CLEANING
        # ---------------------------------------------------------
        # WARNING: This step is deterministic. If regex is too aggressive, we might lose data.
        # Check cleaner.py for specific normalization rules.
        cleaned_text = clean_text(raw_text)
        
        # ---------------------------------------------------------
        # STEP 2: ETL - SECTION EXTRACTION
        # ---------------------------------------------------------
        # Purpose: Break text into manageable chunks (Experience, Education).
        # This helps the LLM focus and reduces Hallucinations.
        sections = extract_sections(cleaned_text)
        
        # Prepare Context for LLM
        # We reconstruct a semi-structured string to guide the model.
        # If extraction failed, we fallback to passing the whole text.
        context_for_llm = ""
        if "raw_content" in sections:
            # Fallback: No specific sections found
            context_for_llm = sections["raw_content"]
        else:
            for title, content in sections.items():
                context_for_llm += f"## {title.upper()}\n{content}\n\n"
        
        # ---------------------------------------------------------
        # STEP 3: LLM - INTELLIGENT TAGGING
        # ---------------------------------------------------------
        # This calls the OpenAI API.
        # WARNING: Cost and Latency implication.
        # The 'tagger' handles the prompt engineering and Pydantic parsing.
        cv_data_obj = tag_cv(context_for_llm)
        
        # ---------------------------------------------------------
        # STEP 4: FORMATTER - OUTPUT
        # ---------------------------------------------------------
        # Enforce the final Schema contract. All fields are typed.
        final_json = format_to_dict(cv_data_obj)
        
        return final_json

# Simple usage example if run directly
if __name__ == "__main__":
    pass
