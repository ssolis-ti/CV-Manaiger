"""
[TEST: DATE PRE-PROCESSOR]
Tests para validar extracción de fechas previa al LLM.
"""
import pytest
from cv_formatter.etl.date_preprocessor import DatePreProcessor, DateHint


class TestDatePreProcessor:
    
    @pytest.fixture
    def preprocessor(self):
        return DatePreProcessor()
    
    def test_extract_spanish_full_range(self, preprocessor):
        """Test: 'Enero 2022 - Presente' -> high confidence"""
        text = "Backend Lead\nEnero 2022 - Presente"
        hints = preprocessor.extract_all_dates(text)
        
        assert 1 in hints
        assert hints[1].start_date == "2022-01"
        assert hints[1].end_date == "Present"
        assert hints[1].confidence == "high"
    
    def test_extract_spanish_date_range(self, preprocessor):
        """Test: 'Marzo 2019 - Diciembre 2021' -> high confidence"""
        text = "Full Stack Developer\nMarzo 2019 - Diciembre 2021"
        hints = preprocessor.extract_all_dates(text)
        
        assert 1 in hints
        assert hints[1].start_date == "2019-03"
        assert hints[1].end_date == "2021-12"
        assert hints[1].confidence == "high"
    
    def test_extract_year_only_range(self, preprocessor):
        """Test: '2020 - 2023' -> high confidence"""
        text = "Manager\n2020 - 2023"
        hints = preprocessor.extract_all_dates(text)
        
        assert 1 in hints
        assert hints[1].start_date == "2020"
        assert hints[1].end_date == "2023"
        assert hints[1].confidence == "high"
    
    def test_extract_year_to_present(self, preprocessor):
        """Test: '2022 - Present' -> high confidence"""
        text = "Director\n2022 - Present"
        hints = preprocessor.extract_all_dates(text)
        
        assert 1 in hints
        assert hints[1].start_date == "2022"
        assert hints[1].end_date == "Present"
    
    def test_no_dates_returns_empty(self, preprocessor):
        """Test: Lines without dates return empty dict"""
        text = "Senior Developer\nPython, Django, AWS"
        hints = preprocessor.extract_all_dates(text)
        
        assert len(hints) == 0
    
    def test_preserves_raw_line(self, preprocessor):
        """Test: Original line is preserved for user review"""
        text = "Role\nEnero 2022 - Presente"
        hints = preprocessor.extract_all_dates(text)
        
        assert hints[1].raw_line == "Enero 2022 - Presente"


# Integration test with real CV format
class TestIntegrationWithCV:
    
    def test_typical_cv_format(self):
        """Test with typical copy-paste CV format"""
        cv_text = """
Juan Perez
Senior Python Developer
Email: juan.perez@email.com

Skills
Python, Django, AWS, Docker, React.js

Experience
Backend Lead @ TechSolutions
Enero 2022 - Presente
- Migración a microservicios

Full Stack Developer @ WebAgency
Marzo 2019 - Diciembre 2021
- Desarrollo de APIs RESTful
"""
        preprocessor = DatePreProcessor()
        hints = preprocessor.extract_all_dates(cv_text)
        
        # Should find at least 2 date ranges
        date_hints = [h for h in hints.values() if h.start_date]
        assert len(date_hints) >= 2
        
        # Verify dates extracted correctly
        dates_found = [(h.start_date, h.end_date) for h in date_hints]
        assert ("2022-01", "Present") in dates_found
        assert ("2019-03", "2021-12") in dates_found
