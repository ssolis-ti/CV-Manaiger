"""
[MODULE: ORCHESTRATION / FACADE]
Role: The 'Conductor'.
Responsibility: Coordinate the pipeline steps (ETL -> LLM -> Formatter).
Flow: 
    1. Receive Raw Text.
    2. Call Cleaner (Normalize).
    3. Call Extractor (Segment).
    4. Call Tagger (Analyze/Structure).
    5. Return Final JSON.
Design Pattern: Facade. Clients (CLI, API) only interact with 'CVProcessor', hiding complexity.
"""
from typing import Dict, Any
import time  # [VIBRATION] Measure the pulse
from cv_formatter.etl.cleaner import clean_text
from cv_formatter.etl.section_extractor import extract_sections
from cv_formatter.llm.tagger import tag_cv
from cv_formatter.formatter.json_formatter import format_to_dict
from cv_formatter.utils.logging_config import setup_logging, get_logger
import json

# setup_logging() should be called by the application entry point (e.g., run_demo.py)
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
        try:
            start_time = time.time()  # [VIBRATION] Measure the pulse
            
            # ---------------------------------------------------------
            # STEP 1: ETL - CLEANING
            # ---------------------------------------------------------
            logger.info("Step 1: ETL Cleaning...")
            cleaned_text = clean_text(raw_text)
            logger.debug(f"Cleaned text length: {len(cleaned_text)} chars")
            
            # ---------------------------------------------------------
            # STEP 2: ETL - SECTION EXTRACTION
            # ---------------------------------------------------------
            # [DIRECTION]: Normalized String -> Dict[SectionName, Content]
            # [LOGIC]: Regex-based splitting to identify "islands" of content.
            logger.info("Step 2: Section Extraction...")
            sections = extract_sections(cleaned_text)
            logger.info(f"Sections found: {list(sections.keys())}")
            
            # Prepare Context for LLM
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
            logger.info("Step 3: LLM Tagging & Analysis...")
            cv_data_obj = tag_cv(context_for_llm)
            
            # ---------------------------------------------------------
            # STEP 4: FORMATTER - OUTPUT
            # ---------------------------------------------------------
            logger.info("Step 4: Formatting Final JSON...")
            final_json = format_to_dict(cv_data_obj)
            
            elapsed = time.time() - start_time
            logger.info(f"Pipeline Completed Successfully in {elapsed:.2f}s.")
            
            return final_json
            
        except Exception as e:
            logger.error(f"Pipeline Failed: {e}")
            raise e

# Simple usage example if run directly
if __name__ == "__main__":
    pass
