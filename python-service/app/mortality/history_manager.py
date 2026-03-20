"""
History Manager - Manages historical quarterly mortality data
Stores and retrieves historical statistics for trend analysis and comparisons
"""

import json
import os
from typing import List, Dict, Optional
from loguru import logger


class HistoryManager:
    """
    Manages historical quarterly mortality data for trend analysis
    """

    def __init__(self, history_file: str = None):
        """
        Initialize HistoryManager

        Args:
            history_file: Path to JSON file storing historical data
        """
        if history_file is None:
            # Default path relative to project root
            self.history_file = os.path.join('storage', 'data', 'mortality_history.json')
        else:
            self.history_file = history_file

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

        # Create file if it doesn't exist
        if not os.path.exists(self.history_file):
            self._create_empty_history()

    def _create_empty_history(self):
        """Create empty history file with sample data"""
        sample_data = [
            {"quarter": "الفصل الثاني", "year": "2025", "rate": 1.46, "deaths": 83},
            {"quarter": "الفصل الاول", "year": "2025", "rate": 2.06, "deaths": 110},
            {"quarter": "الفصل الرابع", "year": "2024", "rate": 1.50, "deaths": 78},
            {"quarter": "الفصل الثالث", "year": "2024", "rate": 1.90, "deaths": 95},
            {"quarter": "الفصل الثاني", "year": "2024", "rate": 1.80, "deaths": 88}
        ]

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 Created history file: {self.history_file}")

    def load_history(self) -> List[Dict]:
        """
        Load all historical quarterly data

        Returns:
            List of historical records, sorted by year and quarter (newest first)
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"📊 Loaded {len(data)} historical records")
            return data

        except FileNotFoundError:
            logger.warning(f"⚠️  History file not found: {self.history_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing history file: {e}")
            return []

    def save_quarter(
        self,
        quarter: str,
        year: str,
        rate: float,
        deaths: int,
        total_patients: int = 0,
        age_groups: List = None,
        departments: Dict = None,
        who_categories: Dict = None
    ):
        """
        Save or update a quarter's full data

        Args:
            quarter: Quarter name (e.g., "الفصل الثالث")
            year: Year as string (e.g., "2025")
            rate: Mortality rate as percentage (e.g., 1.79)
            deaths: Total number of deaths
            total_patients: Total hospital admissions
            age_groups: List of 8 counts matching age categories
            departments: Dict of department_name → death count
            who_categories: Dict of category_name → count
        """
        history = self.load_history()

        # Check if quarter already exists
        existing_idx = None
        for i, record in enumerate(history):
            if record['quarter'] == quarter and record['year'] == year:
                existing_idx = i
                break

        new_record = {
            "quarter": quarter,
            "year": year,
            "rate": round(rate, 2),
            "deaths": deaths,
            "total_patients": total_patients,
            "age_groups": age_groups or [],
            "departments": departments or {},
            "who_categories": who_categories or {}
        }

        if existing_idx is not None:
            history[existing_idx] = new_record
            logger.info(f"📝 Updated: {quarter} {year} - {rate}% ({deaths} deaths)")
        else:
            history.append(new_record)
            logger.info(f"Added: {quarter} {year} - {rate}% ({deaths} deaths)")

        # Save back to file
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _quarter_sort_key(self, record: Dict) -> tuple:
        """Get sort key (year, quarter_num) for chronological ordering."""
        quarter_order = {
            "الفصل الأول": 1, "الفصل الاول": 1,
            "الفصل الثاني": 2,
            "الفصل الثالث": 3,
            "الفصل الرابع": 4
        }
        try:
            year_num = int(record.get('year', '0'))
            quarter_num = quarter_order.get(record.get('quarter', ''), 0)
            return (year_num, quarter_num)
        except (ValueError, TypeError):
            return (0, 0)

    def get_last_n_quarters(self, n: int, current_quarter: str, current_year: str) -> List[Dict]:
        """
        Get last n quarters that came before the current quarter chronologically.

        Args:
            n: Number of quarters to retrieve
            current_quarter: Current quarter to exclude (e.g., "الفصل الثالث")
            current_year: Current year to exclude (e.g., "2025")

        Returns:
            List of n most recent quarters (before current), newest first
        """
        history = self.load_history()
        current_key = self._quarter_sort_key({'quarter': current_quarter, 'year': current_year})

        # Only include quarters that are strictly before the current quarter
        filtered = [
            record for record in history
            if self._quarter_sort_key(record) < current_key
        ]

        # Sort by year and quarter descending (newest first)
        filtered.sort(key=self._quarter_sort_key, reverse=True)

        # Return first n records (no padding — charts handle variable lengths)
        result = filtered[:n]

        logger.debug(f"Retrieved last {len(result)} quarters (requested {n})")

        return result

    def get_previous_quarter(self, current_quarter: str, current_year: str) -> Optional[Dict]:
        """
        Get the immediately previous quarter's data

        Args:
            current_quarter: Current quarter (e.g., "الفصل الثالث")
            current_year: Current year (e.g., "2025")

        Returns:
            Previous quarter's data, or None if not found
        """
        # Quarter order mapping
        quarter_order = {
            "الفصل الاول": 1,
            "الفصل الثاني": 2,
            "الفصل الثالث": 3,
            "الفصل الرابع": 4
        }

        quarter_names = {
            1: "الفصل الاول",
            2: "الفصل الثاني",
            3: "الفصل الثالث",
            4: "الفصل الرابع"
        }

        try:
            current_q_num = quarter_order.get(current_quarter)
            current_y_num = int(current_year)

            # Calculate previous quarter
            if current_q_num == 1:
                # Previous is Q4 of previous year
                prev_quarter = "الفصل الرابع"
                prev_year = str(current_y_num - 1)
            else:
                # Previous quarter in same year
                prev_quarter = quarter_names[current_q_num - 1]
                prev_year = current_year

            # Find in history
            history = self.load_history()
            for record in history:
                if record['quarter'] == prev_quarter and record['year'] == prev_year:
                    logger.debug(f"📊 Found previous quarter: {prev_quarter} {prev_year}")
                    return record

            logger.warning(f"⚠️  Previous quarter not found: {prev_quarter} {prev_year}")
            return None

        except (ValueError, KeyError) as e:
            logger.error(f"❌ Error calculating previous quarter: {e}")
            return None

    def get_quarter_position(self, quarter: str, year: str) -> tuple:
        """
        Get position of a quarter for sorting purposes

        Args:
            quarter: Quarter name (e.g., "الفصل الثالث")
            year: Year as string (e.g., "2025")

        Returns:
            Tuple of (year_num, quarter_num) for sorting
        """
        quarter_order = {
            "الفصل الأول": 1, "الفصل الاول": 1,
            "الفصل الثاني": 2,
            "الفصل الثالث": 3,
            "الفصل الرابع": 4
        }

        try:
            year_num = int(year)
            quarter_num = quarter_order.get(quarter, 0)
            return (year_num, quarter_num)
        except ValueError:
            return (0, 0)


# Singleton instance
history_manager = HistoryManager()
