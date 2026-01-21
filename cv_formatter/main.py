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
import time
from cv_formatter.etl.cleaner import clean_text
from cv_formatter.etl.section_extractor import extract_sections
from cv_formatter.etl.triage import TriageDaemon
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
    
    def __init__(self):
        self.triage_daemon = TriageDaemon()

    def process_cv(self, raw_text: str) -> dict:
        """
        Main entry point (Facade Method).
        Orchestrates the pipeline from Raw Text -> Final JSON.
        """
        try:
            start_time = time.time()
            
            # ---------------------------------------------------------
            # STEP 0: TRIAGE - GATEKEEPER (Phase 6)
            # ---------------------------------------------------------
            logger.info("Step 0: Triage Check...")
            is_valid, reason, meta_context = self.triage_daemon.triage(raw_text)
            
            if not is_valid:
                logger.warning(f"Triage Rejected: {reason}")
                raise ValueError(f"Document rejected by Triage: {reason}")
                
            detected_lang = meta_context.get('language', 'es')
            logger.info(f"Triage Accepted. Language: {detected_lang}")
            
            # ---------------------------------------------------------
            # STEP 0.5: ATS CHECKER
            # ---------------------------------------------------------
            logger.info("Step 0.5: ATS Compliance Audit...")
            from cv_formatter.etl.ats_checker import ATSChecker
            ats_checker = ATSChecker()
            ats_result = ats_checker.check(raw_text)
            logger.info(f"ATS Score: {ats_result.score}/100. Issues: {len(ats_result.issues)}")
            
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
            
            # Prepare Context for LLM (Robust Approach)
            # We send the FULL cleaned text to ensure nothing is lost due to mis-segmentation.
            # We include the section keys as hints for the model.
            header_hint = f"CV Layout Analysis: Found sections {list(sections.keys())}\n\n"
            context_for_llm = header_hint + "### CV CONTENT ###\n" + cleaned_text
            
            # ---------------------------------------------------------
            # STEP 3: LLM - INTELLIGENT TAGGING (With Resilience)
            # ---------------------------------------------------------
            # [DIRECTION]: Structured String -> Pydantic Model (CVData)
            logger.info("Step 3: LLM Tagging & Analysis...")
            
            # [CIRCUIT BREAKER]
            # Try LLM first. If it crashes (500/429) or returns empty, switch to Heuristic.
            try:
                cv_data_obj = tag_cv(context_for_llm, language=detected_lang)
            except Exception as e:
                logger.error(f"LLM Tagging Service Failed: {e}")
                logger.warning("⚠ API Crash detected. Activating Heuristic Fallback immediately.")
                cv_data_obj = None

            # [FALLBACK CHECK]
            # 1. If cv_data_obj is None (API Crash)
            # 2. OR If cv_data_obj.experience is empty (Parsing Failure)
            if not cv_data_obj or not cv_data_obj.experience:
                logger.warning("Attempting Heuristic Fallback (Regex-based)...")
                from cv_formatter.etl.heuristic_extractor import HeuristicExtractor
                heuristic = HeuristicExtractor()
                fallback_data = heuristic.extract(raw_text)
                
                if not cv_data_obj:
                    # Case 1: Total Replacement
                    cv_data_obj = fallback_data
                else:
                    # Case 2: Merge (Keep LLM metadata if valid, but fill Experience)
                    cv_data_obj.experience = fallback_data.experience
                    cv_data_obj.full_name = cv_data_obj.full_name or fallback_data.full_name
            
            # [INJECTION]: Attach ATS Result and Raw Text to the Object
            cv_data_obj.ats_analysis = ats_result
            cv_data_obj.raw_text = raw_text
            
            # ---------------------------------------------------------
            # STEP 4: FORMATTER - OUTPUT
            # ---------------------------------------------------------
            logger.info("Step 4: Formatting Final JSON...")
            final_json = format_to_dict(cv_data_obj)
            
            # ---------------------------------------------------------
            # STEP 5: ENRICHMENT (LAYER 2) - GEMMA 3
            # ---------------------------------------------------------
            # [PATIENCE STRATEGY]: Mandatory 15s delay to avoid API saturation
            logger.info("Step 5: Waiting 15 seconds (Grace Period) before Enrichment...")
            time.sleep(15)
            
            logger.info("Proceeding with Enrichment (Gemma 3)...")
            from cv_formatter.enricher.engine import EnrichmentService
            enricher = EnrichmentService()
            
            # Use the ID generated by Pydantic in the Source JSON
            cv_id = final_json.get('id')
            
            enrichment_obj = enricher.enrich_cv(final_json, cv_id)
            enrichment_json = enrichment_obj.model_dump(exclude_none=True) if enrichment_obj else None
            
            elapsed = time.time() - start_time
            if enrichment_json:
                logger.info(f"Pipeline Completed Successfully in {elapsed:.2f}s.")
            else:
                logger.warning(f"Pipeline Completed (Enrichment Result Unavailable) in {elapsed:.2f}s.")
            
            # Return TWIN-JSON Structure
            return {
                "source_cv": final_json,
                "enrichment": enrichment_json
            }
            
        except Exception as e:
            logger.error(f"Pipeline Failed: {e}")
            raise e

# Simple usage example if run directly
if __name__ == "__main__":
    pass
