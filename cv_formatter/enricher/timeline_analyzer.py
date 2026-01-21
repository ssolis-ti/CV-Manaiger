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
        experiences = cv_data.experience
        if not experiences:
            return TimelineAnalysis(total_years_experience=0, avg_tenure_months=0, stability_score=0)
            
        # Sort by start date (ascending)
        sorted_exp = sorted(
            [e for e in experiences if e.start_date],
            key=lambda x: self._parse_date(x.start_date) or date.min
        )
        
        if not sorted_exp:
             return TimelineAnalysis(total_years_experience=0, avg_tenure_months=0, stability_score=0)

        # 1. Total Experience (First Start -> Last End)
        first_start = self._parse_date(sorted_exp[0].start_date)
        last_end = self._get_end_date(sorted_exp[-1].end_date)
        
        total_months_span = 0
        if first_start and last_end:
            total_months_span = (last_end.year - first_start.year) * 12 + (last_end.month - first_start.month)
            
        total_years = round(total_months_span / 12, 1)

        # 2. Tenure & Gaps
        total_role_months = 0
        gaps = []
        role_count = 0
        
        last_role_end = None
        
        for exp in sorted_exp:
            start = self._parse_date(exp.start_date)
            end = self._get_end_date(exp.end_date)
            
            if not start: continue
            
            # Gap Check (if not overlapping)
            if last_role_end and start > last_role_end:
                gap_months = (start.year - last_role_end.year) * 12 + (start.month - last_role_end.month)
                if gap_months > 6:
                    gaps.append(f"Gap detected: {last_role_end.strftime('%b %Y')} – {start.strftime('%b %Y')} ({gap_months} months)")
            
            # Update last end (handle overlaps)
            if last_role_end is None or end > last_role_end:
                last_role_end = end

            # Tenure
            role_months = (end.year - start.year) * 12 + (end.month - start.month)
            if role_months < 1: role_months = 1
            total_role_months += role_months
            role_count += 1
            
        avg_tenure = int(total_role_months / role_count) if role_count > 0 else 0
        job_hopping = avg_tenure < 12 and role_count > 2
        
        # Stability Score (Heuristic)
        # Base 10. Minus points for gaps and job hopping.
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

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parses YYYY-MM or YYYY-MM-DD string to date object."""
        if not date_str: return None
        try:
            # Try YYYY-MM
            return datetime.strptime(date_str[:7], "%Y-%m").date()
        except ValueError:
            return None

    def _get_end_date(self, date_str: str) -> date:
        """Handles 'Present' / None as Today."""
        if not date_str or date_str.lower() in ['present', 'actualidad', 'presente', 'current']:
            return date.today()
        parsed = self._parse_date(date_str)
        return parsed if parsed else date.today()
