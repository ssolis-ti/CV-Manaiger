import pytest
from cv_formatter.etl.triage import TriageDaemon

@pytest.fixture
def triage_daemon():
    return TriageDaemon()

def test_classify_valid_cv(triage_daemon):
    text = """
    Juan Perez
    Experience
    Senior Developer at Google.
    Skills
    Python, Java.
    """
    assert triage_daemon.classify_document(text) == True

def test_classify_invalid_text(triage_daemon):
    text = "This is just a random note about grocery shopping. Milk, eggs, bread."
    assert triage_daemon.classify_document(text) == False

def test_detect_language_es(triage_daemon):
    text = "Hola, esto es un texto en español para probar la detección de idioma."
    assert triage_daemon.detect_language(text) == 'es'

def test_detect_language_en(triage_daemon):
    text = "Hello, this is an English text for testing language detection."
    assert triage_daemon.detect_language(text) == 'en'

def test_fast_meta_extraction(triage_daemon):
    text = """
    Curriculum Vitae
    Maria Gonzalez
    Email: maria.gonzalez@example.com
    
    Experiencia...
    """
    meta = triage_daemon.fast_extract_meta(text)
    assert meta['email'] == "maria.gonzalez@example.com"
    assert meta['name_candidate'] == "Maria Gonzalez"

def test_triage_flow(triage_daemon):
    text = """
    John Doe
    Software Engineer
    john@example.com
    
    Experience
    DevOps at AWS
    Skills
    Linux, Bash
    """
    is_valid, reason, meta = triage_daemon.triage(text)
    assert is_valid == True
    assert meta['email'] == "john@example.com"
