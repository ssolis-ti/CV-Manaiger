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
    from unittest.mock import MagicMock, patch
    from cv_formatter.etl.semantic_structurer import ExtractedCV, ExperienceItem, TechnicalSkills
    
    # Create the mock result
    mock_cv = ExtractedCV(
        full_name="Juan Perez",
        professional_summary="Senior Python Developer",
        experience=[
            ExperienceItem(
                company="TechSolutions",
                title="Backend Lead",
                start_date="Enero 2022",
                end_date="Presente",
                description="Migración de arquitectura monolítica..."
            ),
            ExperienceItem(
                company="WebAgency",
                title="Full Stack Developer",
                start_date="Marzo 2019",
                end_date="Diciembre 2021",
                description="Desarrollo de APIs RESTful..."
            )
        ],
        skills=TechnicalSkills(
            hard_skills=["Python", "Django", "AWS", "Docker", "React.js"],
            soft_skills=[],
            languages=[]
        )
    )

    # Patch the structurer method
    with patch('cv_formatter.etl.semantic_structurer.SemanticStructurer.extract_structure', return_value=mock_cv):
        processor = CVProcessor()
        # This will now use the mock
        return processor.process_cv(raw_text)

@pytest.fixture(scope="session")
def cv_data(cv_processing_result):
    from cv_formatter.formatter.json_formatter import CVData
    # Return a Pydantic model so the tests can use dot notation (e.g. cv_data.experience)
    return CVData(**cv_processing_result["source_cv"])
