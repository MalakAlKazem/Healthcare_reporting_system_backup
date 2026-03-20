"""
Shared Infection Control Chart Generator for CLABSI and CAUTI reports.

Generates per-floor charts:
  1. Rate trend over recent quarters (line chart + target line)
  2. Germ distribution comparison: current vs previous quarter (grouped bar)
"""

import io
from typing import Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# ── Arabic text reshaping ─────────────────────────────────────────────────────
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _HAS_ARABIC = True
except ImportError:
    _HAS_ARABIC = False
    logger.warning("arabic_reshaper / python-bidi not installed — Arabic labels may render incorrectly")


def _ar(text: str) -> str:
    """Reshape and apply BiDi algorithm so matplotlib renders Arabic correctly."""
    if not text:
        return text
    if _HAS_ARABIC:
        return get_display(arabic_reshaper.reshape(text))
    return text


# ── Font setup ────────────────────────────────────────────────────────────────
# Arial supports Arabic on Windows; fall back to DejaVu Sans if absent
_ARABIC_FONT = 'Arial'

matplotlib.rcParams.update({
    'font.family':        _ARABIC_FONT,
    'axes.unicode_minus': False,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
})

BLUE   = '#4472C4'
ORANGE = '#ED7D31'
RED    = '#C00000'
GRAY   = '#A9A9A9'
GREEN  = '#70AD47'

# ── Arabic label maps ─────────────────────────────────────────────────────────
_QUARTER_AR = {
    1: 'الفصل الأول',  2: 'الفصل الثاني',
    3: 'الفصل الثالث', 4: 'الفصل الرابع',
    'الفصل الأول':  'الفصل الأول',  'الفصل الاول':  'الفصل الأول',
    'الفصل الثاني': 'الفصل الثاني',
    'الفصل الثالث': 'الفصل الثالث',
    'الفصل الرابع': 'الفصل الرابع',
}


def _buf(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


def _quarter_label(q, y) -> str:
    """Full Arabic quarter label for chart x-axis, e.g. 'الفصل الأول 2025'."""
    q_full = _QUARTER_AR.get(q, str(q))
    return _ar(f'{q_full} {y}')


class InfectionControlChartGenerator:
    """
    Generates CLABSI/CAUTI charts for all floors that have data.

    Usage:
        gen    = InfectionControlChartGenerator('CLABSI', 'catheter_days')
        charts = gen.generate_all_charts(history, targets)
        # charts = {'floor_trend_ICU': BytesIO, 'floor_germs_ICU': BytesIO, ...}
    """

    def __init__(self, indicator_name: str, days_key: str):
        self.indicator = indicator_name
        self.days_key  = days_key

    # ──────────────────────────────────────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────────────────────────────────────

    def generate_all_charts(self, history: list, targets: dict) -> dict:
        """
        Generate trend + germs charts for every floor that appears in data.

        Args:
            history : List of history records (CLABSI or CAUTI format)
            targets : {floor: target_rate} dict

        Returns:
            dict of chart_key → BytesIO
        """
        if not history:
            return {}

        # Collect all floors that ever appear
        all_floors: set = set()
        for entry in history:
            all_floors.update(entry.get('summary', {}).keys())

        charts: dict = {}
        for floor in sorted(all_floors):
            trend = self._trend_chart(floor, history, targets)
            if trend:
                charts[f'floor_trend_{floor}'] = trend

            germs = self._germs_chart(floor, history)
            if germs:
                charts[f'floor_germs_{floor}'] = germs

        logger.info(f"{self.indicator}: generated {len(charts)} charts "
                    f"for {len(all_floors)} floors")
        return charts

    # ──────────────────────────────────────────────────────────────────────────
    # Private — trend chart
    # ──────────────────────────────────────────────────────────────────────────

    def _trend_chart(self, floor: str, history: list,
                     targets: dict) -> Optional[io.BytesIO]:
        """Rate-over-quarters line chart for one floor."""
        try:
            labels, rates = [], []
            for entry in history[-5:]:
                summary = entry.get('summary', {})
                if floor not in summary:
                    continue
                q = entry.get('quarter', '')
                y = str(entry.get('year', ''))
                labels.append(_quarter_label(q, y))
                rates.append(float(summary[floor].get('rate', 0.0)))

            if not labels:
                return None

            target = float(targets.get(floor, 0))
            x      = list(range(len(labels)))

            fig, ax = plt.subplots(figsize=(7, 3.5))
            ax.set_facecolor('#f8fafc')
            fig.patch.set_facecolor('white')

            # Actual rate line
            rate_label = _ar(f'معدل {self.indicator} (‰)')
            ax.plot(x, rates, color=BLUE, linewidth=2.5, marker='o',
                    markersize=7, markerfacecolor='white', markeredgewidth=2.5,
                    label=rate_label, zorder=3)

            # Target dashed line
            if target > 0:
                target_label = _ar(f'المستهدف: {target}‰')
                ax.axhline(target, color=RED, linewidth=1.5, linestyle='--',
                           label=target_label, zorder=2)

            # Shade above-target area
            if target > 0:
                ax.fill_between(x, rates, target,
                                where=[r > target for r in rates],
                                alpha=0.12, color=RED, interpolate=True)

            # Point labels
            for xi, yi in zip(x, rates):
                ax.annotate(f'{yi:.2f}‰', (xi, yi),
                            textcoords='offset points', xytext=(0, 9),
                            ha='center', fontsize=8.5, color=BLUE, fontweight='bold')

            ax.set_xticks(x)
            ax.set_xticklabels(labels, fontsize=8, rotation=25, ha='right')
            ax.set_ylabel(_ar('المعدل (‰)'), fontsize=10)
            ax.set_ylim(bottom=0)

            title = _ar(f'{floor} — اتجاه معدل {self.indicator}')
            ax.set_title(title, fontsize=12, fontweight='bold', pad=8, loc='right')
            ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout(pad=0.5)
            return _buf(fig)
        except Exception as exc:
            logger.warning(f"Trend chart failed for {floor}: {exc}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # Private — germs chart
    # ──────────────────────────────────────────────────────────────────────────

    def _germs_chart(self, floor: str,
                     history: list) -> Optional[io.BytesIO]:
        """Grouped bar chart: current vs previous quarter germ counts for one floor."""
        try:
            cur_entry  = history[-1]
            prev_entry = history[-2] if len(history) >= 2 else None

            cur_germs  = cur_entry.get('germs_distribution', {}).get(floor, {})
            prev_germs = (prev_entry.get('germs_distribution', {}).get(floor, {})
                          if prev_entry else {})

            all_germs = sorted(
                set(list(cur_germs.keys()) + list(prev_germs.keys())),
                key=lambda g: -cur_germs.get(g, 0)
            )
            if not all_germs:
                return None

            cur_q  = _quarter_label(cur_entry.get('quarter', ''),
                                    cur_entry.get('year', ''))
            prev_q = (_quarter_label(prev_entry.get('quarter', ''),
                                     prev_entry.get('year', ''))
                      if prev_entry else _ar('الفصل السابق'))

            cur_vals  = [cur_germs.get(g, 0)  for g in all_germs]
            prev_vals = [prev_germs.get(g, 0) for g in all_germs]

            # Reshape Arabic germ names
            germ_labels = [_ar(g) for g in all_germs]

            fig, ax = plt.subplots(figsize=(7, 3.5))
            ax.set_facecolor('#f8fafc')
            fig.patch.set_facecolor('white')

            n     = len(all_germs)
            x     = np.arange(n)
            width = 0.35

            bars_prev = ax.bar(x - width / 2, prev_vals, width,
                               label=prev_q, color=ORANGE, alpha=0.85,
                               edgecolor='white')
            bars_cur  = ax.bar(x + width / 2, cur_vals, width,
                               label=cur_q, color=BLUE, alpha=0.85,
                               edgecolor='white')

            for bar in bars_prev:
                h = bar.get_height()
                if h > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                            str(int(h)), ha='center', va='bottom',
                            fontsize=8.5, color='gray')
            for bar in bars_cur:
                h = bar.get_height()
                if h > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                            str(int(h)), ha='center', va='bottom',
                            fontsize=8.5, color=BLUE, fontweight='bold')

            rotation = 30 if n > 4 or max((len(g) for g in all_germs), default=0) > 8 else 0
            ax.set_xticks(x)
            ax.set_xticklabels(germ_labels, rotation=rotation,
                               ha='right' if rotation else 'center', fontsize=9)
            ax.set_ylabel(_ar('عدد الحالات'), fontsize=10)
            ax.set_ylim(bottom=0)

            title = _ar(f'{floor} — توزيع الجراثيم ({self.indicator})')
            ax.set_title(title, fontsize=12, fontweight='bold', pad=8, loc='right')
            ax.legend(fontsize=9, framealpha=0.9)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout(pad=0.5)
            return _buf(fig)
        except Exception as exc:
            logger.warning(f"Germs chart failed for {floor}: {exc}")
            return None
