import pytest
from cv_formatter.etl.cleaner import clean_text

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
