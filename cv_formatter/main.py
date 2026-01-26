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
from cv_formatter.etl.triage import TriageDaemon
from cv_formatter.formatter.json_formatter import format_to_dict
from cv_formatter.utils.logging_config import setup_logging, get_logger
from cv_formatter.utils.logging_config import setup_logging, get_logger
import json

# setup_logging() should be called by the application entry point (e.g., run_demo.py)
logger = get_logger(__name__)

class CVProcessor:
    """
    Facade to process a CV from raw text to structured JSON.
    
    Flow: Raw Text -> Triage -> ATS -> Clean -> Semantic Structure -> Skills -> Enrich -> Output
    """
    
    def __init__(self):
        self.triage_daemon = TriageDaemon()
    
    def process_cv(self, raw_text: str) -> dict:
        """
        Main entry point (Facade Method).
        Orchestrates the Entity-First Pipeline.
        """
        try:
            start_time = time.time()
            
            # --- STEP 0: TRIAGE ---
            logger.info("Step 0: Triage Check...")
            is_valid, reason, meta_context = self.triage_daemon.triage(raw_text)
            if not is_valid:
                raise ValueError(f"Document rejected: {reason}")
            logger.info(f"Triage Accepted. Language: {meta_context.get('language', 'es')}")
            
            # --- STEP 0.5: ATS (Audit) ---
            from cv_formatter.etl.ats_checker import ATSChecker
            ats_checker = ATSChecker()
            ats_result = ats_checker.check(raw_text)
            
            # --- STEP 1: CLEANING ---
            cleaned_text = clean_text(raw_text)
            
            # --- STEP 2: SEMANTIC STRUCTURER (One-Shot) ---
            # Radical Simplification: LLM extracts full structure directly.
            logger.info("Step 2: One-Shot Semantic Structurer...")
            
            from cv_formatter.etl.semantic_structurer import SemanticStructurer
            structurer = SemanticStructurer()
            
            try:
                extracted_data = structurer.extract_structure(cleaned_text)
            except Exception as e:
                logger.error(f"Semantic Structuring failed: {e}")
                raise ValueError(f"Semantic Structuring failed: {e}")
            
            # --- STEP 3: CONVERT TO CVData FORMAT ---
            from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry, EducationEntry, CertificationEntry
            import uuid

            logger.info(f"Mapping extracted data to CVData...")
            
            # 3.1 Experience
            experience_entries = []
            for exp in extracted_data.experience:
                # Hybrid description: Prefer full text, fallback to bullets join
                desc_text = exp.description if exp.description else "\n".join(exp.description_bullets)
                
                entry = ExperienceEntry(
                    id=str(uuid.uuid4()),
                    company=exp.company or "Unknown",
                    title=exp.title or "Unknown",
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    description=desc_text or "",
                    skills_used=[],
                    date_confidence="high" if exp.start_date else "low"
                )
                experience_entries.append(entry)
                
            # 3.2 Education
            education_entries = []
            for edu in extracted_data.education:
                entry = EducationEntry(
                    institution=edu.institution or "Unknown",
                    degree=edu.degree or "Unknown",
                    year=edu.year
                )
                education_entries.append(entry)
                
            # 3.3 Certifications
            certification_entries = []
            for cert in extracted_data.certifications:
                entry = CertificationEntry(
                    name=cert.name or "Unknown",
                    issuer=cert.issuer or "Unknown",
                    year=cert.year
                )
                certification_entries.append(entry)
                
            # 3.4 Skills (Direct mapping)
            final_skills = {
                "hard_skills": extracted_data.skills.hard_skills,
                "soft_skills": extracted_data.skills.soft_skills,
                "languages": extracted_data.skills.languages
            }
            
            # Use Extracted Summary/Name if available, else defaults
            final_summary = extracted_data.professional_summary or "Extracted via Entity-First Pipeline"
            final_name = extracted_data.full_name or "Candidate"

            # --- STEP 2.9: COLUMNAR DATE RECOVERY (Heuristic) ---
            # Fix for cases where dates are grouped at the end of the document (Columnar Layouts)
            missing_dates_count = sum(1 for e in experience_entries if not e.start_date)
            if missing_dates_count > 0:
                logger.info(f"Detected {missing_dates_count} items with missing dates. Attempting Global Recovery...")
                try:
                    from cv_formatter.etl.date_preprocessor import DatePreProcessor
                    date_proc = DatePreProcessor()
                    all_ranges = list(date_proc.extract_all_dates(cleaned_text).values())
                    
                    # Filter ranges that look like job durations (not just single years usually, but DateProcessor handles ranges)
                    # We assume the order of dates matches the order of experiences (Concept of 'Reading Order')
                    
                    # Pointer for dates
                    date_idx = 0
                    for entry in experience_entries:
                        if not entry.start_date and date_idx < len(all_ranges):
                            candidate = all_ranges[date_idx]
                            entry.start_date = candidate.start_date
                            entry.end_date = candidate.end_date
                            entry.date_confidence = "inferred_columnar"
                            logger.info(f"Recovered date for '{entry.company}': {entry.start_date} - {entry.end_date}")
                            date_idx += 1
                except Exception as e:
                    logger.warning(f"Date Recovery failed: {e}")

            # --- STEP 3: ASSEMBLE ---
            cv_data = CVData(
                id=str(uuid.uuid4()),
                full_name=final_name,
                summary=final_summary,
                experience=experience_entries,
                education=education_entries,
                certifications=certification_entries,
                skills=final_skills,
                ats_analysis=ats_result,
                raw_text=raw_text,
                metadata={"source": "one-shot-llm"}
            )
            
            # Chronology
            from cv_formatter.utils.timeline_sorter import TimelineSorter
            cv_data = TimelineSorter.sort(cv_data)

            # --- STEP 4: FORMAT ---
            final_json = format_to_dict(cv_data)
            
            # --- STEP 5: ENRICHMENT (LAYER 2) ---
            logger.info("Proceeding with Enrichment (Gemma 3)...")
            enrichment_json = None
            
            try:
                from cv_formatter.enricher.engine import EnrichmentService
                enricher = EnrichmentService()
                
                # Get ID from source
                cv_id = final_json.get('id')
                
                enrichment_obj = enricher.enrich_cv(final_json, cv_id)
                enrichment_json = enrichment_obj.model_dump(exclude_none=True) if enrichment_obj else None
                
            except Exception as e:
                logger.warning(f"Enrichment service unavailable: {e}")

            elapsed = time.time() - start_time
            if enrichment_json:
                logger.info(f"Pipeline Completed Successfully in {elapsed:.2f}s")
            else:
                logger.info(f"Pipeline Completed (Source Only) in {elapsed:.2f}s")
            
            # Return TWIN-JSON Structure
            return {
                "source_cv": final_json,
                "enrichment": enrichment_json
            }
            
        except Exception as e:
            logger.error(f"Pipeline Fatal Error: {str(e)}", exc_info=True)
            raise e

# Simple usage example if run directly
if __name__ == "__main__":
    pass
