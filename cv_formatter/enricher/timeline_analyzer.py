"""
[MODULE: TIMELINE ANALYZER]
Role: The 'Actuary'.
Responsibility: Calculate temporal statistics from CV Experience data.
Flow: Experience List -> Date Parsing -> Gaps/Tenure Calculation.
Logic:
- Deterministic parsing of dates (YYYY-MM).
- Gap logic: > 6 months between roles.
- Tenure logic: Sum of all role durations? Or time since first role?
"""
from datetime import datetime, date
from typing import List, Optional, Tuple
from cv_formatter.formatter.json_formatter import CVData, ExperienceEntry
from cv_formatter.enricher.schemas import TimelineAnalysis

class TimelineAnalyzer:
    
    def analyze(self, cv_data: CVData) -> TimelineAnalysis:
        from cv_formatter.utils.date_normalizer import DateNormalizer
        experiences = cv_data.experience
        if not experiences:
            return TimelineAnalysis(total_years_experience=0, avg_tenure_months=0, stability_score=0)
            
        # Parse all dates first
        parsed_entries = []
        for e in experiences:
            start = DateNormalizer.parse_to_date(e.start_date)
            end = DateNormalizer.parse_to_date(e.end_date, is_end_date=True)
            if start:
                parsed_entries.append({'start': start, 'end': end, 'entry': e})

        if not parsed_entries:
            return TimelineAnalysis(total_years_experience=0, avg_tenure_months=0, stability_score=0)

        # Sort by start date (ascending)
        sorted_parsed = sorted(parsed_entries, key=lambda x: x['start'])
        
        # 1. Total Experience (First Start -> Last End)
        first_start = sorted_parsed[0]['start']
        # Find the latest end date among all entries
        latest_end = max([x['end'] for x in sorted_parsed])
        
        total_months_span = (latest_end.year - first_start.year) * 12 + (latest_end.month - first_start.month)
        total_years = round(total_months_span / 12, 1) if total_months_span > 0 else 0.1

        # 2. Tenure & Gaps
        total_role_months = 0
        gaps = []
        role_count = 0
        last_role_end = None
        
        for item in sorted_parsed:
            start = item['start']
            end = item['end']
            
            # Gap Check
            if last_role_end and start > last_role_end:
                gap_months = (start.year - last_role_end.year) * 12 + (start.month - last_role_end.month)
                if gap_months > 6:
                    gaps.append(f"Gap detected: {last_role_end.strftime('%b %Y')} – {start.strftime('%b %Y')} ({gap_months} months)")
            
            # Update last end
            if last_role_end is None or end > last_role_end:
                last_role_end = end

            # Tenure
            role_months = (end.year - start.year) * 12 + (end.month - start.month)
            if role_months < 1: role_months = 1
            total_role_months += role_months
            role_count += 1
            
        avg_tenure = int(total_role_months / role_count) if role_count > 0 else 0
        job_hopping = avg_tenure < 12 and role_count > 2
        
        # Stability Score
        score = 10
        if job_hopping: score -= 3
        score -= len(gaps) * 2
        if score < 1: score = 1
        
        return TimelineAnalysis(
            total_years_experience=total_years,
            avg_tenure_months=avg_tenure,
            detected_gaps=gaps,
            job_hopping_risk=job_hopping,
            stability_score=score
        )

import re # Ensure re is imported if not already in global scope or add to imports
