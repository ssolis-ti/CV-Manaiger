import pytest
import json
from cv_formatter.formatter.json_formatter import CVData

# Mock or Real Data needed for these tests
# For now, we define the structure of the tests as requested
# Ideally, these would run against a "Golden Dataset" of CVs

def test_dates_present_if_exist(raw_text, cv_data: CVData):
    """
    Test 1 – Fechas no opcionales
    If the raw text contains obvious date indicators (Years 202x, Months),
    The CV Data MUST have extracted start_date/end_date in its experience entries.
    """
    date_indicators = ["2020", "2021", "2022", "2023", "2024", "2025", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    has_dates_in_text = any(indicator in raw_text for indicator in date_indicators)
    
    if has_dates_in_text and cv_data.experience:
        # Check that at least one experience entry has a date
        has_extracted_dates = any(
            e.start_date is not None 
            for e in cv_data.experience
        )
        assert has_extracted_dates, "Raw text had dates, but none were extracted into Experience Entries."

def test_hard_skills_extracted(cv_data: CVData):
    """
    Test 2 – Skills no vacías
    Schematron MUST extract hard skills if they exist. 
    It is statistically impossible for a Technical CV to have 0 hard skills.
    """
    # Assuming the input was technical
    assert len(cv_data.skills.hard_skills) > 0, "Hard Skills list is empty. Extraction failed or Rule ignored."

def test_no_inferred_data_in_cv(cv_data: CVData):
    """
    Test 3 – Separation of concerns
    The Source CV (Facts) should not contain coaching language or inferred gaps.
    """
    # Check Summary for "meta-commentary"
    if cv_data.summary:
        forbidden_terms = ["missing", "recommend", "should learn", "gap detected", "fit for role"]
        summary_clean = cv_data.summary.lower()
        for term in forbidden_terms:
            assert term not in summary_clean, f"Found coaching term '{term}' in Source CV Summary. This belongs in Enrichment."

# Note: To run these, we need a fixture that loads a sample result.
# For example:
# @pytest.fixture
# def sample_result():
#     return process_cv_files(sample_path)
