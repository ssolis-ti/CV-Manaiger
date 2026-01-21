import pytest
from cv_formatter.etl.ats_checker import ATSChecker

@pytest.fixture
def ats_checker():
    return ATSChecker()

def test_no_issues(ats_checker):
    text = """
    Juan Perez
    Experience
    Developer
    Skills
    Java
    Education
    BS
    """
    result = ats_checker.check(text)
    assert result.score == 100
    assert len(result.issues) == 0

def test_emojis_penalty(ats_checker):
    text = "Developer 🚀🔥"
    result = ats_checker.check(text)
    # 2 emojis * 2 points = 4 penalty. Missing sections = 40 penalty
    assert "Found 2 emojis/icons" in result.issues[0]
    assert result.score < 100

def test_weird_bullets_penalty(ats_checker):
    text = """
    Experience
    ➤ Task 1
    ➤ Task 2
    ➤ Task 3
    ➤ Task 4
    ➤ Task 5
    ➤ Task 6
    """
    result = ats_checker.check(text)
    assert any("Excessive use of non-standard bullet" in i for i in result.issues)
    assert result.score <= 90

def test_missing_sections(ats_checker):
    text = "Just a name and nothing else."
    result = ats_checker.check(text)
    assert "Experience/Experience" in result.missing_sections
    assert "Skills/Habilidades" in result.missing_sections
    assert result.score <= 60
