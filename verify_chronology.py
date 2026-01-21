import asyncio
import json
from datetime import date
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry
from cv_formatter.utils.date_normalizer import DateNormalizer
from cv_formatter.utils.timeline_sorter import TimelineSorter
from cv_formatter.enricher.timeline_analyzer import TimelineAnalyzer

async def test_date_robustness():
    print("=== Testing DateNormalizer Robustness ===")
    test_dates = [
        "Marzo 2023", "03/2023", "2023-03", "Mar 2023", "March 2023",
        "Presente", "Actualidad", "Current", "Jan 2024", "2024"
    ]
    for d in test_dates:
        normalized = DateNormalizer.normalize(d)
        parsed = DateNormalizer.parse_to_date(d)
        print(f"Raw: {d} -> Normalized: {normalized} -> Parsed: {parsed}")

async def test_chronology_sorting():
    print("\n=== Testing TimelineSorter (Chronology) ===")
    cv_data = CVData(
        full_name="Test Candidate",
        experience=[
            ExperienceEntry(title="Oldest Job", company="A", start_date="2010", end_date="2012", description=""),
            ExperienceEntry(title="Recent Job", company="B", start_date="2020", end_date="Present", description=""),
            ExperienceEntry(title="Middle Job", company="C", start_date="2015", end_date="2018", description=""),
        ]
    )
    
    sorted_cv = TimelineSorter.sort(cv_data)
    print("Sorted Order (Expected: Recent -> Middle -> Oldest):")
    for exp in sorted_cv.experience:
        print(f" - {exp.title} ({exp.start_date} to {exp.end_date})")

async def test_timeline_analyzer():
    print("\n=== Testing TimelineAnalyzer (Experience Score) ===")
    cv_data = CVData(
        full_name="Test Candidate",
        experience=[
            ExperienceEntry(title="Job 1", company="A", start_date="Jan 2020", end_date="Dec 2022", description=""),
            ExperienceEntry(title="Job 2", company="B", start_date="Feb 2023", end_date="Present", description=""),
        ]
    )
    
    analyzer = TimelineAnalyzer()
    analysis = analyzer.analyze(cv_data)
    print(f"Total Years Experience: {analysis.total_years_experience}")
    print(f"Average Tenure: {analysis.avg_tenure_months} months")
    print(f"Stability Score: {analysis.stability_score}")

if __name__ == "__main__":
    asyncio.run(test_date_robustness())
    asyncio.run(test_chronology_sorting())
    asyncio.run(test_timeline_analyzer())
