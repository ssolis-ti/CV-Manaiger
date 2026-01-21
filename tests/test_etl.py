import pytest
from cv_formatter.etl.cleaner import clean_text
from cv_formatter.etl.section_extractor import extract_sections

def test_clean_text_normalization():
    # Test whitespace and bullet normalization
    raw_text = "  Developer  \t with   \u2022 Python "
    expected = "Developer with - Python"
    assert clean_text(raw_text) == expected

def test_clean_text_newlines():
    # Test newline reduction
    raw_text = "Line 1\n\n\nLine 2"
    expected = "Line 1\n\nLine 2"
    assert clean_text(raw_text) == expected

def test_extract_sections_basic():
    # Test basic section extraction
    text = """
    John Doe
    Software Engineer
    
    Experiencia:
    Senior Dev at Tech Corp
    2020 - Present
    
    Educación
    BS CS, University of Tech
    """
    cleaned = clean_text(text)
    sections = extract_sections(cleaned)
    
    assert "experience" in sections
    assert "education" in sections
    assert "header_info" in sections
    
    assert "john doe" in sections["header_info"].lower()
    assert "tech corp" in sections["experience"].lower()
    assert "university" in sections["education"].lower()

def test_extract_sections_english_fallback():
    text = """
    Summary
    Expert coder.
    
    Experience
    DevOps
    """
    cleaned = clean_text(text)
    sections = extract_sections(cleaned)
    
    assert "experience" in sections
    assert "devops" in sections["experience"].lower()
