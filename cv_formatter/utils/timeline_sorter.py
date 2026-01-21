from typing import List
from datetime import date
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry
from cv_formatter.utils.date_normalizer import DateNormalizer

class TimelineSorter:
    """
    Ensures CV experience entries are sorted chronologically (latest first).
    Handles 'Present' correctly as the most recent date.
    """
    
    @staticmethod
    def sort(cv_data: CVData) -> CVData:
        if not cv_data.experience:
            return cv_data
            
        def get_sort_key(entry: ExperienceEntry):
            # Parse start date for sorting
            # We use start_date for primary sorting, but end_date (if 'Present') for ties?
            # Usually, you want the most recent JOB at the top.
            # Most recent job = job with latest end_date.
            
            start = DateNormalizer.parse_to_date(entry.start_date) or date.min
            end = DateNormalizer.parse_to_date(entry.end_date, is_end_date=True) or date.min
            
            # Sort by end date primarily (descending), then start date (descending)
            return (end, start)
            
        cv_data.experience.sort(key=get_sort_key, reverse=True)
        return cv_data
