from cv_formatter.etl.cleaner import clean_text
from cv_formatter.etl.section_extractor import extract_sections
from cv_formatter.llm.tagger import tag_cv
from cv_formatter.formatter.json_formatter import format_to_dict
from cv_formatter.utils.logging_config import setup_logging, get_logger
import json

setup_logging() # Ensure logging is setup when module is imported or run
logger = get_logger(__name__)

class CVProcessor:
    """
    Facade to process a CV from raw text to structured JSON.
    """
    
    def process_cv(self, raw_text: str) -> dict:
        """
        Main entry point (Facade Method).
        Orchestrates the pipeline from Raw Text -> Final JSON.
        """
        logger.info("Starting CV Processing Pipeline")
        logger.debug(f"Input text length: {len(raw_text)} chars")
        
        # ---------------------------------------------------------
        # STEP 1: ETL - CLEANING
        # ---------------------------------------------------------
        # [DIRECTION]: Input Raw String -> Output Normalized String
        # [LOGIC]: Remove visual noise (bullets, wide spaces) to help Regex/LLM.
        # [WARNING/POSSIBLE BUG]: If the user pastes a PDF parsed text with headers/footers 
        # mixed in line-by-line, the cleaner currently does NOT re-assemble paragraphs easily. 
        # This might fragment sentences.
        logger.info("Step 1: ETL Cleaning...")
        cleaned_text = clean_text(raw_text)
        logger.debug(f"Cleaned text length: {len(cleaned_text)} chars")
        
        # ---------------------------------------------------------
        # STEP 2: ETL - SECTION EXTRACTION
        # ---------------------------------------------------------
        # [DIRECTION]: Normalized String -> Dict[SectionName, Content]
        # [LOGIC]: Regex-based splitting to identify "islands" of content.
        # [POSSIBLE BUG]: Heuristic dependency. If a CV uses creative headers like 
        # "My Journey" instead of "Experience", this extraction will FAIL to separate it,
        # fallbacking to "raw_content". The LLM usually handles this, but it increases token cost.
        logger.info("Step 2: Section Extraction...")
        sections = extract_sections(cleaned_text)
        logger.info(f"Sections found: {list(sections.keys())}")
        
        # Prepare Context for LLM
        # [REDIRECTION]: We re-assemble the text but tagged with Markdown headers 
        # to force the LLM to see the structure we found.
        context_for_llm = ""
        if "raw_content" in sections:
            logger.warning("No specific sections identified. Using raw content for LLM.")
            context_for_llm = sections["raw_content"]
        else:
            for title, content in sections.items():
                context_for_llm += f"## {title.upper()}\n{content}\n\n"
        
        # ---------------------------------------------------------
        # STEP 3: LLM - INTELLIGENT TAGGING (With Resilience)
        # ---------------------------------------------------------
        # [DIRECTION]: Structured String -> Pydantic Model (CVData)
        # [LOGIC]: OpenAI (GPT-4o) parses the text and standardizes it into our Schema.
        # [ROBUSTNESS]: Wrapped in Tenacity for network retries.
        # [POSSIBLE BUG]: Context Window Limit. If input > 128k tokens, this call crashes.
        # Currently handled by basic token counting log, but not strict truncation.
        logger.info("Step 3: LLM Tagging & Analysis (OpenAI)...")
        cv_data_obj = tag_cv(context_for_llm)
        
        # ---------------------------------------------------------
        # STEP 4: FORMATTER - OUTPUT
        # ---------------------------------------------------------
        logger.info("Step 4: Formatting Final JSON...")
        final_json = format_to_dict(cv_data_obj)
        
        logger.info("Pipeline Completed Successfully.")
        return final_json

# Simple usage example if run directly
if __name__ == "__main__":
    pass
