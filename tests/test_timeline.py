import pytest
from datetime import date
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry
from cv_formatter.enricher.timeline_analyzer import TimelineAnalyzer

@pytest.fixture
def timeline_analyzer():
    return TimelineAnalyzer()

def test_empty_cv(timeline_analyzer):
    cv = CVData(full_name="Empty")
    res = timeline_analyzer.analyze(cv)
    assert res.total_years_experience == 0
    assert res.avg_tenure_months == 0
    assert res.stability_score == 0

def test_simple_career(timeline_analyzer):
    cv = CVData(full_name="Junior")
    cv.experience = [
        ExperienceEntry(title="Job 1", start_date="2020-01", end_date="2021-01"), # 12 months
        ExperienceEntry(title="Job 2", start_date="2021-02", end_date="Present"), # ~Now
    ]
    # Mocking 'Present' would require freezing time, but _get_end_date uses date.today()
    # Let's assume date.today() is > 2021-02.
    
    res = timeline_analyzer.analyze(cv)
    assert res.total_years_experience > 1.0
    assert len(res.detected_gaps) == 0

def test_gap_detection(timeline_analyzer):
    cv = CVData(full_name="Gappy")
    cv.experience = [
        ExperienceEntry(title="Job 1", start_date="2018-01", end_date="2019-01"),
        # Gap: Jan 2019 to Jan 2020 (12 months)
        ExperienceEntry(title="Job 2", start_date="2020-01", end_date="2021-01"),
    ]
    res = timeline_analyzer.analyze(cv)
    assert len(res.detected_gaps) == 1
    assert "2019" in res.detected_gaps[0]
    
def test_job_hopping(timeline_analyzer):
    cv = CVData(full_name="Hopper")
    cv.experience = [
        ExperienceEntry(title="Job 1", start_date="2020-01", end_date="2020-03"),
        ExperienceEntry(title="Job 2", start_date="2020-04", end_date="2020-06"),
        ExperienceEntry(title="Job 3", start_date="2020-07", end_date="2020-09"),
    ]
    res = timeline_analyzer.analyze(cv)
    assert res.job_hopping_risk == True
    assert res.avg_tenure_months < 6
