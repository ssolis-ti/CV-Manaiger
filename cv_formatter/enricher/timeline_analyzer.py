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
        """Robustly parses dates like 'YYYY-MM', 'MM/YYYY', 'Mar 2023', 'Marzo 2023'."""
        if not date_str: return None
        
        # 1. Standardize (Remove periods, comma, spaces)
        clean = date_str.lower().replace('.', '').replace(',', '').strip()
        
        # 2. Try YYYY-MM or YYYY-MM-DD
        try:
            return datetime.strptime(clean[:7], "%Y-%m").date()
        except: pass
        
        # 3. Handle Month Year (ES/EN)
        months_map = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
            'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12,
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        # Regex to find Year and Month
        year_match = re.search(r'(\d{4})', clean)
        if not year_match: return None
        year = int(year_match.group(1))
        
        # Look for month name in string
        month = 1 # Default to Jan
        for name, val in months_map.items():
            if name in clean:
                month = val
                break
        else:
            # Maybe it's numeric MM/YYYY?
            month_match = re.search(r'(\d{1,2})[/\- ]', clean)
            if month_match:
                m = int(month_match.group(1))
                if 1 <= m <= 12: month = m
                
        return date(year, month, 1)

    def _get_end_date(self, date_str: str) -> date:
        """Handles 'Present' / None as Today."""
        if not date_str: 
            return date.today()
        
        val = date_str.lower()
        if any(w in val for w in ['present', 'actualidad', 'presente', 'current', 'ahora']):
            return date.today()
            
        parsed = self._parse_date(date_str)
        return parsed if parsed else date.today()

import re # Ensure re is imported if not already in global scope or add to imports
