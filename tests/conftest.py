import pytest
import sys
import os

# Ensure we can import the project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cv_formatter.main import CVProcessor
from cv_formatter.formatter.json_formatter import CVData

@pytest.fixture(scope="session")
def raw_text():
    return """
Juan Perez
Senior Python Developer
Email: juan.perez@email.com

Skills
Python, Django, AWS, Docker, React.js

Experience
Backend Lead @ TechSolutions
Enero 2022 - Presente
- Migración de arquitectura monolítica a microservicios usando Docker y Kubernetes.

Full Stack Developer @ WebAgency
Marzo 2019 - Diciembre 2021
- Desarrollo de APIs RESTful con Flask.
"""

@pytest.fixture(scope="session")
def cv_processing_result(raw_text):
    processor = CVProcessor()
    # Process the CV. This might make an API call depending on implementation.
    # If the system uses a real LLM, this will cost money/tokens.
    # Ideally we should mock the LLM, but for an "Integrity" test on a "Stable MVP", 
    # we might want the real deal or a recorded response.
    # Given the instructions "refuses to invent dates", it implies testing the LLM logic.
    return processor.process_cv(raw_text)

@pytest.fixture(scope="session")
def cv_data(cv_processing_result):
    from cv_formatter.formatter.json_formatter import CVData
    # Return a Pydantic model so the tests can use dot notation (e.g. cv_data.experience)
    return CVData(**cv_processing_result["source_cv"])
