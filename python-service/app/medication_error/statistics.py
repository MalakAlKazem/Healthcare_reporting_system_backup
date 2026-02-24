"""
Medication Error Statistics Calculator - FULLY FIXED
All calculations use error_count column for proper weighting
All auto-corrections are case-insensitive
"""

import pandas as pd
from typing import Dict
from loguru import logger


class MedicationErrorStatistics:
    """Calculate medication error statistics with proper weighting"""
    
    def __init__(self):
        self.stats = {}
    
    def calculate_all_statistics(self, df: pd.DataFrame, total_doses: int, 
                                 quarter: str, year: int) -> Dict:
        """Calculate complete statistics for medication errors"""
        logger.info("📊 Calculating medication error statistics...")
        
        # Calculate total errors - sum error_count column
        if 'error_count' in df.columns:
            total_errors = int(df['error_count'].sum())
        else:
            total_errors = len(df)
        
        error_rate = round((total_errors / total_doses) * 100, 4)
        
        stats = {
            'summary': {
                'quarter': quarter,
                'year': year,
                'error_rate': error_rate,
                'total_errors': total_errors,
                'total_doses': total_doses,
                'target': 0.03
            },
            'error_cycle': self._calculate_error_cycle(df),
            'detected_by': self._calculate_detection(df),
            'duty_shift': self._calculate_duty_shift(df),
            'staff_involved': self._calculate_staff_involved(df),
            'error_causes': self._calculate_error_causes(df),
            'error_types': self._calculate_error_types(df),
            'departments': self._calculate_departments(df),
            'ncc_merp': self._calculate_ncc_merp(df),
            'cause_stage_matrix': self._calculate_cause_stage_matrix(df),
            'type_stage_matrix': self._calculate_type_stage_matrix(df),
            'departments_all': self._calculate_departments_all(df),
        }
        
        logger.success(f"✅ Statistics calculated - Error rate: {error_rate}%")
        self.stats = stats
        return stats
    
    def _calculate_error_cycle(self, df: pd.DataFrame) -> Dict:
        """Chart 3 - Error cycle with error_count weighting"""
        if 'error_cycle' not in df.columns:
            return {'counts': {}, 'percentages': {}, 'total': 0}
        
        df_clean = df.copy()
        
        # Case-insensitive standardization
        def standardize_cycle(val):
            val = str(val).lower().strip()
            if 'prescri' in val:
                return 'Prescribing'
            elif 'transcri' in val:
                return 'Transcription'
            elif 'dispens' in val:
                return 'Dispensing'
            elif 'admin' in val:
                return 'Administration'
            elif 'monitor' in val:
                return 'Monitoring'
            elif 'prepar' in val:
                return 'Preparation'
            return val.title() if val else 'Unknown'
        
        df_clean['cycle_clean'] = df_clean['error_cycle'].apply(standardize_cycle)
        
        # Weighted counts
        if 'error_count' in df_clean.columns:
            counts = df_clean.groupby('cycle_clean')['error_count'].sum().to_dict()
        else:
            counts = df_clean['cycle_clean'].value_counts().to_dict()
        
        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }
    
    def _calculate_detection(self, df: pd.DataFrame) -> Dict:
        """Chart 4 - Detection method with error_count weighting"""
        detection_col = 'detected_by' if 'detected_by' in df.columns else None
        
        if not detection_col:
            for col in df.columns:
                if 'detect' in col.lower():
                    detection_col = col
                    break
        
        if not detection_col:
            return {'counts': {}, 'percentages': {}, 'total': 0}
        
        df_clean = df.copy()
        
        # Case-insensitive auto-correct
        def standardize_detection(val):
            val = str(val).lower().strip()
            
            if 'pharmacist' in val or 'pharm' in val:
                return 'Pharmacist'
            elif val.startswith('rn') or ('nurse' in val and 'head' not in val):
                return 'RN'
            elif 'hn' in val or 'head nurse' in val:
                return 'HN'
            elif 'physician' in val or 'doctor' in val or val.startswith('dr'):
                return 'Physician'
            
            return val.title() if val else 'Unknown'
        
        df_clean['detected_clean'] = df_clean[detection_col].apply(standardize_detection)
        
        # Weighted counts
        if 'error_count' in df_clean.columns:
            counts = df_clean.groupby('detected_clean')['error_count'].sum().to_dict()
        else:
            counts = df_clean['detected_clean'].value_counts().to_dict()
        
        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }
    
    def _calculate_duty_shift(self, df: pd.DataFrame) -> Dict:
        """Chart 5 - Duty shift with error_count weighting"""
        col = 'duty_full' if 'duty_full' in df.columns else ('duty' if 'duty' in df.columns else None)
        
        if not col:
            return {'counts': {}, 'percentages': {}, 'total': 0}
        
        df_clean = df.copy()
        
        # Case-insensitive auto-correct
        def standardize_duty(val):
            val = str(val).lower().strip()
            if val in ['am', 'd', 'day']:
                return 'Day'
            elif val in ['pm', 'e', 'evening']:
                return 'Evening'
            elif val in ['n', 'night']:
                return 'Night'
            return val.title() if val else 'Unknown'
        
        df_clean['duty_clean'] = df_clean[col].apply(standardize_duty)
        
        # Weighted counts
        if 'error_count' in df_clean.columns:
            counts = df_clean.groupby('duty_clean')['error_count'].sum().to_dict()
        else:
            counts = df_clean['duty_clean'].value_counts().to_dict()
        
        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }
    
    def _calculate_staff_involved(self, df: pd.DataFrame) -> Dict:
        """Chart 6 - Staff involved with error_count weighting"""
        if 'job_title' not in df.columns:
            return {'counts': {}, 'percentages': {}, 'total': 0}
        
        df_clean = df.copy()
        
        # Case-insensitive auto-correct (including spelling fixes)
        def standardize_staff(val):
            val = str(val).lower().strip()
            
            if 'physician' in val or val.startswith('dr') or 'doctor' in val:
                return 'Physician'
            elif val == 'rn' or 'registered nurse' in val:
                return 'RN'
            elif 'pharm' in val:  # Catches "pharmasist", "pharmacist"
                return 'Pharmacist'
            elif 'hn' in val or 'head nurse' in val:
                return 'HN'
            
            return val.title() if val else 'Unknown'
        
        df_clean['staff_clean'] = df_clean['job_title'].apply(standardize_staff)
        
        # Weighted counts
        if 'error_count' in df_clean.columns:
            counts = df_clean.groupby('staff_clean')['error_count'].sum().to_dict()
        else:
            counts = df_clean['staff_clean'].value_counts().to_dict()
        
        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }
    
    def _calculate_error_causes(self, df: pd.DataFrame) -> Dict:
        """Chart 7 - Error causes with error_count weighting, case-insensitive"""
        cause_col = 'error_cause' if 'error_cause' in df.columns else None
        
        if not cause_col:
            for col in df.columns:
                if 'cause' in col.lower():
                    cause_col = col
                    break
        
        if not cause_col:
            return {'counts': {}, 'percentages': {}, 'total': 0}
        
        df_clean = df.copy()
        
        # Clean and standardize (case-insensitive grouping)
        df_clean['cause_clean'] = df_clean[cause_col].fillna('Unknown').astype(str).str.strip()
        
        # Group by lowercase, then convert to title case for display
        df_clean['cause_lower'] = df_clean['cause_clean'].str.lower()
        
        # Weighted counts grouped by lowercase
        if 'error_count' in df_clean.columns:
            counts_lower = df_clean.groupby('cause_lower')['error_count'].sum()
        else:
            counts_lower = df_clean['cause_lower'].value_counts()
        
        # Get top 6
        top_causes_lower = counts_lower.nlargest(6)
        
        # Convert back to proper display names (title case)
        counts = {}
        for cause_lower, count in top_causes_lower.items():
            # Find original case from data
            original = df_clean[df_clean['cause_lower'] == cause_lower]['cause_clean'].iloc[0]
            counts[original] = int(count)
        
        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }
    
    def _calculate_error_types(self, df: pd.DataFrame) -> Dict:
        """Error types distribution"""
        type_col = 'error_type' if 'error_type' in df.columns else None
        
        if not type_col:
            for col in df.columns:
                if 'type' in col.lower() and 'error' in col.lower():
                    type_col = col
                    break
        
        if not type_col:
            return {'counts': {}, 'percentages': {}, 'total': 0}
        
        df_clean = df.copy()
        
        # Weighted counts
        if 'error_count' in df_clean.columns:
            counts = df_clean.groupby(type_col)['error_count'].sum().nlargest(10).to_dict()
        else:
            counts = df_clean[type_col].value_counts().head(10).to_dict()
        
        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }
    
    def _calculate_departments(self, df: pd.DataFrame) -> Dict:
        """Department distribution"""
        if 'nursing_unit' not in df.columns:
            return {'counts': {}, 'percentages': {}, 'total': 0}

        # Weighted counts
        if 'error_count' in df.columns:
            counts = df.groupby('nursing_unit')['error_count'].sum().nlargest(20).to_dict()
        else:
            counts = df['nursing_unit'].value_counts().head(20).to_dict()

        total = sum(counts.values())
        return {
            'counts': counts,
            'percentages': {k: round((v/total)*100, 1) for k, v in counts.items()},
            'total': int(total)
        }

    def _calculate_ncc_merp(self, df: pd.DataFrame) -> Dict:
        """
        NCC MERP classification breakdown.
        Groups 'error_count' by 'error_category' (mapped from Excel 'Error Category').
        Normalises raw values like 'A', 'B', 'Category A', 'category b' → 'Category X'.
        """
        if 'error_category' not in df.columns:
            return {'counts': {}, 'percentages': {}, 'total': 0}

        VALID = {'A', 'B', 'C', 'D', 'E', 'F'}

        def standardize(val):
            s = str(val).strip().upper()
            # "Category B" or "CATEGORY B"
            if s.startswith('CATEGORY '):
                letter = s[len('CATEGORY '):].strip()
                if letter in VALID:
                    return f'Category {letter}'
            # bare letter "B"
            if s in VALID:
                return f'Category {s}'
            return None   # unrecognised — skip

        df_clean = df.copy()
        df_clean['ncc_clean'] = df_clean['error_category'].apply(standardize)
        df_clean = df_clean[df_clean['ncc_clean'].notna()]

        if df_clean.empty:
            return {'counts': {}, 'percentages': {}, 'total': 0}

        if 'error_count' in df_clean.columns:
            counts = df_clean.groupby('ncc_clean')['error_count'].sum().to_dict()
        else:
            counts = df_clean['ncc_clean'].value_counts().to_dict()

        counts = {k: int(v) for k, v in counts.items()}
        total  = sum(counts.values())
        return {
            'counts':      counts,
            'percentages': {k: round((v / total) * 100, 1) for k, v in counts.items()},
            'total':       total,
        }

    def _calculate_cause_stage_matrix(self, df: pd.DataFrame) -> Dict:
        """
        Cross-tabulation: Cause of Error (rows) × Stage of Process (columns).
        - 'Transcription' and 'Administration' are merged into one column.
        - All causes from the data are included (sorted by row total descending).
        - Any unexpected stage values are appended after the preferred order.

        Returns:
            causes      – ordered list of cause labels
            stages      – ordered list of stage labels (merged columns)
            matrix      – {cause: {stage: count}}
            row_totals  – {cause: total}
            col_totals  – {stage: total}
            grand_total – int
        """
        CAUSE_COL = 'error_cause'
        STAGE_COL = 'error_cycle'

        if CAUSE_COL not in df.columns or STAGE_COL not in df.columns:
            return {
                'causes': [], 'stages': [], 'matrix': {},
                'row_totals': {}, 'col_totals': {}, 'grand_total': 0,
            }

        # Preferred stage display order
        STAGE_ORDER = [
            'Prescribing',
            'Transcription & Administration',
            'Dispensing',
            'Preparation',
            'Monitoring',
        ]

        def normalize_stage(val):
            s = str(val).strip().lower()
            if 'prescri'  in s: return 'Prescribing'
            if 'transcri' in s: return 'Transcription & Administration'
            if 'admin'    in s: return 'Transcription & Administration'
            if 'dispens'  in s: return 'Dispensing'
            if 'monitor'  in s: return 'Monitoring'
            if 'prepar'   in s: return 'Preparation'
            return str(val).strip().title()

        df_clean = df.copy()
        df_clean['stage_norm'] = df_clean[STAGE_COL].apply(normalize_stage)

        # Normalise cause: strip + lowercase key, title-case display label
        df_clean['cause_raw']  = df_clean[CAUSE_COL].fillna('Unknown').astype(str).str.strip()
        df_clean['cause_key']  = df_clean['cause_raw'].str.lower()

        # Build a display label map: lowercase key → title-case label
        cause_label = {}
        for raw, key in zip(df_clean['cause_raw'], df_clean['cause_key']):
            if key not in cause_label:
                cause_label[key] = raw.title() if raw else 'Unknown'

        # Weighted pivot grouped by (cause_key, stage_norm)
        if 'error_count' in df_clean.columns:
            pivot = df_clean.pivot_table(
                index='cause_key', columns='stage_norm',
                values='error_count', aggfunc='sum', fill_value=0
            )
        else:
            pivot = df_clean.pivot_table(
                index='cause_key', columns='stage_norm',
                aggfunc='size', fill_value=0
            )

        actual_stages  = list(pivot.columns)
        ordered_stages = [s for s in STAGE_ORDER if s in actual_stages]
        extra_stages   = [s for s in actual_stages if s not in STAGE_ORDER]
        ordered_stages = ordered_stages + extra_stages
        pivot = pivot.reindex(columns=ordered_stages, fill_value=0)

        cause_keys = list(pivot.index)
        matrix = {
            cause_label[key]: {stage: int(pivot.loc[key, stage]) for stage in ordered_stages}
            for key in cause_keys
        }
        causes      = list(matrix.keys())
        row_totals  = {cause: int(sum(matrix[cause].values())) for cause in causes}
        col_totals  = {
            stage: int(sum(matrix[cause].get(stage, 0) for cause in causes))
            for stage in ordered_stages
        }
        grand_total = int(sum(row_totals.values()))

        # Sort causes by row total descending
        causes_sorted = sorted(causes, key=lambda c: row_totals[c], reverse=True)

        return {
            'causes':      causes_sorted,
            'stages':      ordered_stages,
            'matrix':      matrix,
            'row_totals':  row_totals,
            'col_totals':  col_totals,
            'grand_total': grand_total,
        }

    def _calculate_type_stage_matrix(self, df: pd.DataFrame) -> Dict:
        """
        Cross-tabulation: Type of Error (rows) × Stage of Process (columns).
        - 'Transcription' and 'Administration' are merged into one column.
        - All types from the data are included (sorted by row total descending).
        - Any unexpected stage values are appended after the preferred order.

        Returns:
            types       – ordered list of type labels
            stages      – ordered list of stage labels (merged columns)
            matrix      – {type: {stage: count}}
            row_totals  – {type: total}
            col_totals  – {stage: total}
            grand_total – int
        """
        TYPE_COL  = 'error_type'
        STAGE_COL = 'error_cycle'

        if TYPE_COL not in df.columns or STAGE_COL not in df.columns:
            return {
                'types': [], 'stages': [], 'matrix': {},
                'row_totals': {}, 'col_totals': {}, 'grand_total': 0,
            }

        STAGE_ORDER = [
            'Prescribing',
            'Transcription & Administration',
            'Dispensing',
            'Preparation',
            'Monitoring',
        ]

        def normalize_stage(val):
            s = str(val).strip().lower()
            if 'prescri'  in s: return 'Prescribing'
            if 'transcri' in s: return 'Transcription & Administration'
            if 'admin'    in s: return 'Transcription & Administration'
            if 'dispens'  in s: return 'Dispensing'
            if 'monitor'  in s: return 'Monitoring'
            if 'prepar'   in s: return 'Preparation'
            return str(val).strip().title()

        df_clean = df.copy()
        df_clean['stage_norm'] = df_clean[STAGE_COL].apply(normalize_stage)

        # Normalise type: strip + lowercase key, title-case display label
        df_clean['type_raw'] = df_clean[TYPE_COL].fillna('Unknown').astype(str).str.strip()
        df_clean['type_key'] = df_clean['type_raw'].str.lower()

        # Build a display label map: lowercase key → title-case label
        type_label = {}
        for raw, key in zip(df_clean['type_raw'], df_clean['type_key']):
            if key not in type_label:
                type_label[key] = raw.title() if raw else 'Unknown'

        # Weighted pivot grouped by (type_key, stage_norm)
        if 'error_count' in df_clean.columns:
            pivot = df_clean.pivot_table(
                index='type_key', columns='stage_norm',
                values='error_count', aggfunc='sum', fill_value=0
            )
        else:
            pivot = df_clean.pivot_table(
                index='type_key', columns='stage_norm',
                aggfunc='size', fill_value=0
            )

        actual_stages  = list(pivot.columns)
        ordered_stages = [s for s in STAGE_ORDER if s in actual_stages]
        extra_stages   = [s for s in actual_stages if s not in STAGE_ORDER]
        ordered_stages = ordered_stages + extra_stages
        pivot = pivot.reindex(columns=ordered_stages, fill_value=0)

        type_keys = list(pivot.index)
        matrix = {
            type_label[key]: {stage: int(pivot.loc[key, stage]) for stage in ordered_stages}
            for key in type_keys
        }
        types       = list(matrix.keys())
        row_totals  = {t: int(sum(matrix[t].values())) for t in types}
        col_totals  = {
            stage: int(sum(matrix[t].get(stage, 0) for t in types))
            for stage in ordered_stages
        }
        grand_total = int(sum(row_totals.values()))

        # Sort types by row total descending
        types_sorted = sorted(types, key=lambda t: row_totals[t], reverse=True)

        return {
            'types':       types_sorted,
            'stages':      ordered_stages,
            'matrix':      matrix,
            'row_totals':  row_totals,
            'col_totals':  col_totals,
            'grand_total': grand_total,
        }

    def _calculate_departments_all(self, df: pd.DataFrame) -> Dict:
        """
        All nursing units with their ME counts.
        - NaN / empty strings → '(blank)'
        - Sorted alphabetically (case-insensitive), '(blank)' last.

        Returns:
            units  – ordered list of unit labels
            counts – {unit: count}
            total  – grand total
        """
        if 'nursing_unit' not in df.columns:
            return {'units': [], 'counts': {}, 'total': 0}

        df_clean = df.copy()
        df_clean['unit_clean'] = (
            df_clean['nursing_unit']
            .fillna('(blank)')
            .astype(str)
            .str.strip()
        )
        df_clean.loc[df_clean['unit_clean'] == '', 'unit_clean'] = '(blank)'

        if 'error_count' in df_clean.columns:
            counts_s = df_clean.groupby('unit_clean')['error_count'].sum()
        else:
            counts_s = df_clean['unit_clean'].value_counts()

        counts = {k: int(v) for k, v in counts_s.items()}
        total  = int(sum(counts.values()))

        # Alphabetical sort, case-insensitive; '(blank)' goes last
        def _sort_key(k):
            return ('zzz', k) if k == '(blank)' else (k.lower(), k)

        units_sorted = sorted(counts.keys(), key=_sort_key)

        return {'units': units_sorted, 'counts': counts, 'total': total}