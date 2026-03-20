"""
VAP Chart Generator
Generates all 6 VAP charts dynamically from statistics + history data.

Charts
------
1  – ICU  VAP rate trend      (line, last 5 quarters, target 25‰)
2  – ICU  germs comparison    (grouped bar, current vs previous quarter)
3  – CCU  VAP rate trend      (line, last 4 quarters, target 15‰)
4  – CCU  germs comparison    (grouped bar, current vs previous quarter)
5  – ICN  VAP rate trend      (line, last 4 quarters, target 10‰)
6  – ICN  germs comparison    (grouped bar, current vs previous quarter)

Usage
-----
    from vap_chart_generator import VAPChartGenerator
    from vap_history import VAPHistory

    hist   = VAPHistory('storage/data/VAP_history.json')
    charts = hist.get_chart_data()
    gen    = VAPChartGenerator(output_dir='storage/charts')
    bufs   = gen.generate_all_charts(charts)
    # bufs = { 'chart1_icu_trend': BytesIO, ... }
"""

import io
import math
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    logger.warning("arabic-reshaper / python-bidi not installed — Arabic text disabled")

matplotlib.rcParams.update({
    'font.family':         'DejaVu Sans',
    'axes.unicode_minus':  False,
    'axes.spines.top':     False,
    'axes.spines.right':   False,
})

# ── Palette (matches existing medication error charts) ────────────────────────
BLUE   = '#4472C4'
ORANGE = '#ED7D31'
GREEN  = '#70AD47'
GRAY   = '#A9A9A9'

# ── Quarter display names (Arabic → short label) ─────────────────────────────
QUARTER_AR = {
    'first':  'الأول',   'First':  'الأول',
    'second': 'الثاني',  'Second': 'الثاني',
    'third':  'الثالث',  'Third':  'الثالث',
    'fourth': 'الرابع',  'Fourth': 'الرابع',
    # Already-Arabic passthrough
    'الاول':  'الأول',   'الأول':  'الأول',
    'الثاني': 'الثاني',
    'الثالث': 'الثالث',
    'الرابع': 'الرابع',
}


def _ar(text: str) -> str:
    """Reshape + bidi-correct Arabic text for Matplotlib."""
    if not ARABIC_SUPPORT or not text:
        return str(text)
    try:
        if '\n' in text:
            return '\n'.join(
                get_display(arabic_reshaper.reshape(line)) if line.strip() else line
                for line in text.split('\n')
            )
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return str(text)


def _quarter_label(entry: Dict) -> str:
    """{ quarter: 'Third', year: '2025' }  →  'الثالث\\n2025'"""
    q   = str(entry.get('quarter', ''))
    yr  = str(entry.get('year', ''))
    ar_q = QUARTER_AR.get(q, q)
    return f"{ar_q}\n{yr}"


def _to_buf(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


def _legend_label(quarter: str, year: str, language: str = 'ar') -> str:
    """Build legend label:  'نسبة حالات الـ VAP+germs خلال الفصل الثاني من العام 2025'"""
    ar_q = QUARTER_AR.get(quarter, quarter)
    if language == 'ar':
        return _ar(f"نسبة حالات الـ VAP+germs خلال الفصل {ar_q} من العام {year}")
    return f"VAP+germs — {quarter} {year}"


# ═════════════════════════════════════════════════════════════════════════════
# LINE CHART  (Charts 1, 3, 5)
# ═════════════════════════════════════════════════════════════════════════════

def _line_chart(
    trend_data: List[Dict],
    floor_label: str,
    target: float,
    figsize=(8, 4),
) -> io.BytesIO:
    """
    Generic VAP rate trend line chart.

    Parameters
    ----------
    trend_data  : list from get_floor_trend() —
                  [{ quarter, year, rate, target, cases, ventilator_days }, ...]
    floor_label : e.g. 'ICU'
    target      : horizontal target line value (‰)
    """
    if not trend_data:
        logger.warning(f"_line_chart: no data for {floor_label}")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        return _to_buf(fig)

    x      = np.arange(len(trend_data))
    values = [round(d['rate'], 2) for d in trend_data]
    labels = [_ar(_quarter_label(d)) for d in trend_data]

    # Y-axis ceiling: at least target × 1.4, or max_value × 1.4
    y_max = max(max(values) if values else 0, target) * 1.4
    y_max = math.ceil(y_max / 2) * 2   # round up to nearest even number

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # ── Floor rate line ───────────────────────────────────────────────────────
    ax.plot(x, values, marker='o', color=BLUE, linewidth=2,
            markersize=6, markerfacecolor=BLUE, markeredgecolor=BLUE,
            label=floor_label, zorder=3)

    # ── Target line ───────────────────────────────────────────────────────────
    ax.axhline(target, color=ORANGE, linewidth=2, label='Target', zorder=2)

    # ── Value annotations ────────────────────────────────────────────────────
    for xi, val in zip(x, values):
        offset = y_max * 0.035
        ax.annotate(f'{val}‰', (xi, val),
                    textcoords='offset points', xytext=(0, 8),
                    ha='center', fontsize=9, color='#333333')

    # Target label at right end
    ax.annotate(f'{int(target)}‰',
                (x[-1], target),
                textcoords='offset points', xytext=(18, 4),
                ha='left', color=ORANGE, fontsize=9, fontweight='bold')

    # ── Axes ─────────────────────────────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, ha='center')
    ax.set_ylim(0, y_max)
    ax.set_xlim(-0.5, len(trend_data) - 0.5)

    # ── Grid ─────────────────────────────────────────────────────────────────
    ax.grid(True, axis='y', linestyle='-', linewidth=0.6,
            color='#E0E0E0', alpha=0.8, zorder=1)
    ax.set_axisbelow(True)

    # ── Spines ───────────────────────────────────────────────────────────────
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')

    # ── Legend & title ────────────────────────────────────────────────────────
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    ax.set_title(floor_label, fontsize=11, fontweight='bold', pad=10, loc='right')

    plt.tight_layout()
    return _to_buf(fig)


# ═════════════════════════════════════════════════════════════════════════════
# GERMS BAR CHART  (Charts 2, 4, 6)
# ═════════════════════════════════════════════════════════════════════════════

def _germs_bar_chart(
    germs_data: Dict,
    figsize=(9, 5),
) -> io.BytesIO:
    """
    Generic grouped bar chart comparing germ distribution across two quarters.

    Parameters
    ----------
    germs_data : output of get_floor_germs_comparison() —
        {
          germs:    [ 'Germ A', 'Germ B', ... ],   # unified sorted list
          current:  { quarter, year, counts, percentages, labels, total },
          previous: { same } | None
        }
    """
    current  = germs_data.get('current')
    previous = germs_data.get('previous')
    germs    = germs_data.get('germs', [])

    if not current or not germs:
        logger.warning("_germs_bar_chart: no data")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        return _to_buf(fig)

    x     = np.arange(len(germs))
    width = 0.35 if previous else 0.55

    # ── Percentage arrays ──────────────────────────────────────────────────
    cur_pcts  = [current['percentages'].get(g, 0)  for g in germs]
    prev_pcts = [previous['percentages'].get(g, 0) for g in germs] if previous else []

    # ── Count arrays for annotations ──────────────────────────────────────
    cur_counts  = [current['counts'].get(g, 0)  for g in germs]
    prev_counts = [previous['counts'].get(g, 0) for g in germs] if previous else []

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # ── Legend labels ──────────────────────────────────────────────────────
    cur_legend  = _legend_label(current['quarter'],  str(current['year']))
    prev_legend = _legend_label(previous['quarter'], str(previous['year'])) if previous else ''

    if previous:
        # Previous = BLUE (left bar), Current = GREEN (right bar)
        # matches the design: older quarter on left, newer on right
        bars_prev = ax.bar(x - width / 2, prev_pcts, width,
                           color=BLUE,  label=prev_legend, zorder=3)
        bars_cur  = ax.bar(x + width / 2, cur_pcts,  width,
                           color=GREEN, label=cur_legend,  zorder=3)

        for bar, pct, cnt in zip(bars_prev, prev_pcts, prev_counts):
            if pct > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        pct + 1.5, f'{int(pct)}%({cnt})',
                        ha='center', fontsize=8, color='#222222')

        for bar, pct, cnt in zip(bars_cur, cur_pcts, cur_counts):
            if pct > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        pct + 1.5, f'{int(pct)}%({cnt})',
                        ha='center', fontsize=8, color='#222222')
    else:
        # Only current quarter — single bars in GREEN
        bars_cur = ax.bar(x, cur_pcts, width, color=GREEN, label=cur_legend, zorder=3)
        for bar, pct, cnt in zip(bars_cur, cur_pcts, cur_counts):
            if pct > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        pct + 1.5, f'{int(pct)}%({cnt})',
                        ha='center', fontsize=8, color='#222222')

    # ── X-axis labels: wrap long germ names ───────────────────────────────
    import textwrap
    x_labels = ['\n'.join(textwrap.wrap(g, width=16)) for g in germs]

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=8, ha='center', linespacing=1.3)
    ax.set_ylim(0, 120)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f'{int(v)}%'))

    # ── Grid ─────────────────────────────────────────────────────────────
    ax.grid(True, axis='y', linestyle='-', linewidth=0.6,
            color='#E0E0E0', alpha=0.7, zorder=1)
    ax.set_axisbelow(True)

    # ── Spines ───────────────────────────────────────────────────────────
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')

    # ── Legend below chart ────────────────────────────────────────────────
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.22),
              ncol=1, frameon=False, fontsize=8)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.28)
    return _to_buf(fig)


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC CLASS
# ═════════════════════════════════════════════════════════════════════════════

class VAPChartGenerator:
    """
    Generate all 6 VAP charts from the output of VAPHistory.get_chart_data().

    Example
    -------
        hist   = VAPHistory('storage/data/VAP_history.json')
        data   = hist.get_chart_data()
        gen    = VAPChartGenerator(output_dir='storage/charts/vap')
        bufs   = gen.generate_all_charts(data)
        # bufs['chart1_icu_trend']  → BytesIO (PNG)
    """

    FLOOR_TARGETS = {'ICU': 25.0, 'CCU': 15.0, 'ICN': 10.0}

    def __init__(self, output_dir: str = 'storage/charts/vap'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public entry point ────────────────────────────────────────────────────

    def generate_all_charts(self, chart_data: Dict) -> Dict[str, io.BytesIO]:
        """
        Generate all 6 charts and return as BytesIO buffers.

        Parameters
        ----------
        chart_data : output of VAPHistory.get_chart_data()

        Returns
        -------
        {
            'chart1_icu_trend':  BytesIO,
            'chart2_icu_germs':  BytesIO,
            'chart3_ccu_trend':  BytesIO,
            'chart4_ccu_germs':  BytesIO,
            'chart5_icn_trend':  BytesIO,
            'chart6_icn_germs':  BytesIO,
        }
        """
        logger.info("🎨 Generating all 6 VAP charts...")

        bufs = {
            'chart1_icu_trend': self.chart1_icu_trend(chart_data.get('chart1_icu_trend', [])),
            'chart2_icu_germs': self.chart2_icu_germs(chart_data.get('chart2_icu_germs', {})),
            'chart3_ccu_trend': self.chart3_ccu_trend(chart_data.get('chart3_ccu_trend', [])),
            'chart4_ccu_germs': self.chart4_ccu_germs(chart_data.get('chart4_ccu_germs', {})),
            'chart5_icn_trend': self.chart5_icn_trend(chart_data.get('chart5_icn_trend', [])),
            'chart6_icn_germs': self.chart6_icn_germs(chart_data.get('chart6_icn_germs', {})),
        }

        logger.success("✅ All 6 VAP charts generated")
        return bufs

    # ── Chart 1: ICU trend ────────────────────────────────────────────────────

    def chart1_icu_trend(self, trend_data: List[Dict]) -> io.BytesIO:
        """ICU VAP rate trend — last 5 quarters, target 25‰."""
        logger.info("Chart 1: ICU trend...")
        return _line_chart(trend_data, 'ICU', target=25.0, figsize=(8, 4))

    # ── Chart 2: ICU germs ────────────────────────────────────────────────────

    def chart2_icu_germs(self, germs_data: Dict) -> io.BytesIO:
        """ICU germs — current quarter vs previous quarter."""
        logger.info("Chart 2: ICU germs comparison...")
        return _germs_bar_chart(germs_data, figsize=(9, 5))

    # ── Chart 3: CCU trend ────────────────────────────────────────────────────

    def chart3_ccu_trend(self, trend_data: List[Dict]) -> io.BytesIO:
        """CCU VAP rate trend — last 4 quarters, target 15‰."""
        logger.info("Chart 3: CCU trend...")
        return _line_chart(trend_data, 'CCU', target=15.0, figsize=(8, 4))

    # ── Chart 4: CCU germs ────────────────────────────────────────────────────

    def chart4_ccu_germs(self, germs_data: Dict) -> io.BytesIO:
        """CCU germs — current quarter vs previous quarter."""
        logger.info("Chart 4: CCU germs comparison...")
        return _germs_bar_chart(germs_data, figsize=(9, 5))

    # ── Chart 5: ICN trend ────────────────────────────────────────────────────

    def chart5_icn_trend(self, trend_data: List[Dict]) -> io.BytesIO:
        """ICN VAP rate trend — last 4 quarters, target 10‰."""
        logger.info("Chart 5: ICN trend...")
        return _line_chart(trend_data, 'ICN', target=10.0, figsize=(8, 4))

    # ── Chart 6: ICN germs ────────────────────────────────────────────────────

    def chart6_icn_germs(self, germs_data: Dict) -> io.BytesIO:
        """ICN germs — current quarter vs previous quarter."""
        logger.info("Chart 6: ICN germs comparison...")
        return _germs_bar_chart(germs_data, figsize=(9, 5))

    # ── Save helper ───────────────────────────────────────────────────────────

    def save_chart(self, name: str, buf: io.BytesIO) -> Path:
        out = self.output_dir / f"{name}.png"
        buf.seek(0)
        out.write_bytes(buf.read())
        logger.info(f"💾 Saved {out}")
        return out

    def save_all_charts(self, bufs: Dict[str, io.BytesIO]) -> Dict[str, Path]:
        return {name: self.save_chart(name, buf) for name, buf in bufs.items()}
