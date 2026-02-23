"""
Medication Error Chart Generator
Chart styles match Untitled7.ipynb exactly
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import textwrap
from typing import Dict, List
from pathlib import Path
from loguru import logger
import io

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    logger.warning("Arabic support not available")


class MedicationErrorCharts:

    COLORS = {
        'blue':   '#4472C4',
        'orange': '#ED7D31',
        'yellow': '#FFC000',
        'green':  '#70AD47',
        'gray':   '#A5A5A5',
        'light_blue': '#5B9BD5',
    }

    TARGET = 0.03   # T < 0.03 %

    def __init__(self, output_dir: str = 'charts'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'
        matplotlib.rcParams['axes.unicode_minus'] = False

    # ── helpers ──────────────────────────────────────────────────────────────

    def _ar(self, text: str) -> str:
        if not ARABIC_SUPPORT or not text:
            return str(text)
        try:
            t = str(text)
            if '\n' in t:
                return '\n'.join(
                    get_display(arabic_reshaper.reshape(line)) if line.strip() else line
                    for line in t.split('\n')
                )
            return get_display(arabic_reshaper.reshape(t))
        except Exception:
            return str(text)

    def _short_quarter(self, h: Dict) -> str:
        """الفصل الثالث 2025  →  الثالث\n2025"""
        q = h['quarter'].replace('الفصل ', '')
        return f"{q}\n{h['year']}"

    def _to_buf(self, fig) -> io.BytesIO:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf

    # ── public ───────────────────────────────────────────────────────────────

    def generate_all_charts(self, stats: Dict, history: List[Dict]) -> Dict[str, io.BytesIO]:
        logger.info("Generating all 7 charts...")
        charts = {
            'chart1_trend':           self.generate_trend_chart(history),
            'chart2_comparison':      self.generate_comparison_chart(history),
            'chart3_cycle_pie':       self.generate_cycle_pie(stats['error_cycle']),
            'chart4_detection_donut': self.generate_detection_donut(stats['detected_by']),
            'chart5_shift_donut':     self.generate_shift_donut(stats['duty_shift']),
            'chart6_staff_donut':     self.generate_staff_donut(stats['staff_involved']),
            'chart7_causes_bars':     self.generate_causes_bars(stats['error_causes']),
        }
        logger.success("Generated all 7 charts")
        return charts

    # ── Chart 1: Error Rate Trend ─────────────────────────────────────────────

    def generate_trend_chart(self, history: List[Dict]) -> io.BytesIO:
        """Blue result line + orange target line. Y-axis on right. Matches notebook chart 1."""
        logger.info("Chart 1: Medication error trend...")

        # Newest quarter on LEFT → reverse so index 0 = most recent
        recent = list(reversed(history[-11:] if len(history) > 11 else history))

        x            = np.arange(len(recent))
        rates        = [h['error_rate'] for h in recent]
        target_line  = [self.TARGET] * len(recent)
        x_labels     = [self._ar(self._short_quarter(h)) for h in recent]

        fig, ax = plt.subplots(figsize=(16, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Result line
        ax.plot(x, rates, color=self.COLORS['blue'], linewidth=2.5,
                marker='o', markersize=7,
                markerfacecolor=self.COLORS['blue'],
                markeredgecolor=self.COLORS['blue'],
                label=self._ar('النتيجة'), zorder=3)

        # Target line
        ax.plot(x, target_line, color=self.COLORS['orange'], linewidth=2.5,
                linestyle='-', label=self._ar('المستهدف (T)'), zorder=2)

        # Value labels above each point
        for xi, yi in zip(x, rates):
            ax.text(xi, yi + 0.002, f'{yi:.4f}%',
                    ha='center', va='bottom', fontsize=9, color='#333333')

        # Y-axis on right
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position('right')

        # Y-axis range and ticks
        y_max   = max(max(rates), self.TARGET) * 1.4
        y_ticks = np.arange(0, y_max + 0.005, 0.005)
        ax.set_ylim(0, y_max)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels([f'{y:.3f}%' for y in y_ticks], fontsize=9)

        # X-axis
        ax.set_xlim(-0.5, len(recent) - 0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, fontsize=9, ha='center')

        # Title
        ax.set_title('Medication Errors\nT<0.03%',
                     fontsize=16, fontweight='bold', pad=20, color='#333333')

        # Grid horizontal only
        ax.grid(True, axis='y', linestyle='-', linewidth=0.8,
                color='#D3D3D3', alpha=0.7, zorder=1)
        ax.set_axisbelow(True)

        # Spines
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_color('#999999')
        ax.spines['bottom'].set_color('#999999')

        # Legend
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.18),
                  ncol=2, frameon=False, fontsize=11)

        plt.tight_layout()
        return self._to_buf(fig)

    # ── Chart 2: ME Count Comparison ─────────────────────────────────────────

    def generate_comparison_chart(self, history: List[Dict]) -> io.BytesIO:
        """Blue line with count labels. Matches notebook ME comparison chart."""
        logger.info("Chart 2: ME count comparison...")

        # Newest quarter on LEFT → reverse so index 0 = most recent
        recent = list(reversed(history[-11:] if len(history) > 11 else history))

        x       = np.arange(len(recent))
        counts  = [h['total_errors'] for h in recent]
        x_labels = [self._ar(self._short_quarter(h)) for h in recent]

        fig, ax = plt.subplots(figsize=(14, 5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Blue line with markers
        ax.plot(x, counts, color=self.COLORS['blue'], linewidth=3,
                marker='o', markersize=9,
                markerfacecolor=self.COLORS['blue'],
                markeredgecolor='white', markeredgewidth=2, zorder=3)

        # Count labels above each point
        y_offset = max(counts) * 0.05
        for xi, yi in zip(x, counts):
            ax.text(xi, yi + y_offset, str(int(yi)),
                    ha='center', va='bottom',
                    fontsize=13, fontweight='bold', color='#333333')

        # Y-axis on right
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position('right')
        ax.set_ylim(0, max(counts) * 1.3)
        ax.set_yticks([0, 50, 100, 150])

        # X-axis
        ax.set_xlim(-0.5, len(recent) - 0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, fontsize=10, ha='center')

        # Title
        ax.set_title(self._ar('مقارنة عدد ME خلال الفصول'),
                     fontsize=14, pad=20, color='#555555')

        # Grid horizontal only
        ax.grid(True, axis='y', linestyle='-', linewidth=0.8,
                color='#E0E0E0', alpha=0.7, zorder=1)
        ax.set_axisbelow(True)

        # Spines
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')

        plt.tight_layout()
        return self._to_buf(fig)

    # ── Chart 3: Error Cycle Pie ──────────────────────────────────────────────

    def generate_cycle_pie(self, cycle_data: Dict) -> io.BytesIO:
        """3D shadow pie. Colors: blue, orange, yellow, green. Legend bottom center."""
        logger.info("Chart 3: Error cycle pie...")

        counts = cycle_data.get('counts', {})
        if not counts:
            counts = {'Prescribing': 23, 'Transcription': 16,
                      'Administration': 4, 'Dispensing': 2}

        # Sort descending by count so largest slice gets first color (blue)
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        sizes  = [item[1] for item in sorted_items]
        total  = sum(sizes)

        color_order = [self.COLORS['blue'], self.COLORS['orange'],
                       self.COLORS['yellow'], self.COLORS['green']]
        colors  = color_order[:len(labels)]

        # Explode the top 2 slices (largest)
        explode = [0.05 if i < 2 else 0 for i in range(len(labels))]

        fig, ax = plt.subplots(figsize=(9, 7))
        fig.patch.set_facecolor('white')

        ax.pie(
            sizes, labels=None, colors=colors,
            autopct=lambda p: f'{round(p):.0f}%',
            startangle=90,
            explode=explode, shadow=True,
            textprops={'fontsize': 16, 'fontweight': 'bold', 'color': 'white'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        )

        # Legend with count + percentage: "Prescribing (23 - 51%)"
        pct_labels = [
            f'{lb}  ({sz} - {round(sz/total*100):.0f}%)'
            for lb, sz in zip(labels, sizes)
        ]
        ax.legend(pct_labels, loc='lower center', bbox_to_anchor=(0.5, -0.15),
                  ncol=2, frameon=False, fontsize=11)
        ax.axis('equal')
        plt.tight_layout()
        return self._to_buf(fig)

    # ── Chart 4: Detection Donut ──────────────────────────────────────────────

    def generate_detection_donut(self, detection_data: Dict) -> io.BytesIO:
        """Who detected the error — donut. Legend bottom center."""
        logger.info("Chart 4: Detection donut...")

        counts = detection_data.get('counts', {})
        if not counts:
            counts = {'Physician': 49, 'RN': 44, 'Pharmacist': 7}

        labels = list(counts.keys())
        sizes  = list(counts.values())
        colors = [self.COLORS['light_blue'], self.COLORS['orange'],
                  self.COLORS['gray']][:len(labels)]

        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')

        ax.pie(sizes, labels=None, colors=colors,
               autopct='%d%%', startangle=90,
               textprops={'fontsize': 16, 'fontweight': 'bold', 'color': 'white'},
               wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'width': 0.5},
               pctdistance=0.75)

        # White center hole
        ax.add_artist(plt.Circle((0, 0), 0.50, fc='white'))

        legend_labels = [f'{lb} (result id)' for lb in labels]
        ax.legend(legend_labels, loc='lower center', bbox_to_anchor=(0.5, -0.12),
                  ncol=3, frameon=False, fontsize=10)
        ax.axis('equal')
        plt.tight_layout()
        return self._to_buf(fig)

    # ── Chart 5: Shift Donut ──────────────────────────────────────────────────

    def generate_shift_donut(self, shift_data: Dict) -> io.BytesIO:
        """Day / Evening / Night donut."""
        logger.info("Chart 5: Shift donut...")

        counts = shift_data.get('counts', {})
        if not counts:
            counts = {'Day': 76, 'Evening': 9, 'Night': 16}

        labels = list(counts.keys())
        sizes  = list(counts.values())
        colors = [self.COLORS['light_blue'], self.COLORS['orange'],
                  self.COLORS['gray']][:len(labels)]

        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')

        ax.pie(sizes, labels=None, colors=colors,
               autopct='%d%%', startangle=90,
               textprops={'fontsize': 16, 'fontweight': 'bold', 'color': 'white'},
               wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'width': 0.5},
               pctdistance=0.75)

        ax.add_artist(plt.Circle((0, 0), 0.50, fc='white'))

        ax.legend(labels, loc='lower center', bbox_to_anchor=(0.5, -0.12),
                  ncol=3, frameon=False, fontsize=12)
        ax.axis('equal')
        plt.tight_layout()
        return self._to_buf(fig)

    # ── Chart 6: Staff Donut ──────────────────────────────────────────────────

    def generate_staff_donut(self, staff_data: Dict) -> io.BytesIO:
        """Staff involved — donut. RN / Pharmacist / Physician."""
        logger.info("Chart 6: Staff donut...")

        counts = staff_data.get('counts', {})
        if not counts:
            counts = {'RN': 80, 'Pharmacist': 16, 'Physician': 4}

        labels = list(counts.keys())
        sizes  = list(counts.values())
        colors = [self.COLORS['orange'], self.COLORS['gray'],
                  self.COLORS['light_blue']][:len(labels)]

        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')

        ax.pie(sizes, labels=None, colors=colors,
               autopct='%d%%', startangle=90,
               textprops={'fontsize': 16, 'fontweight': 'bold', 'color': 'white'},
               wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'width': 0.5},
               pctdistance=0.75)

        ax.add_artist(plt.Circle((0, 0), 0.50, fc='white'))

        legend_labels = [f'{lb} (result id)' for lb in labels]
        ax.legend(legend_labels, loc='lower center', bbox_to_anchor=(0.5, -0.12),
                  ncol=3, frameon=False, fontsize=11)
        ax.axis('equal')
        plt.tight_layout()
        return self._to_buf(fig)

    # ── Chart 7: Contributing Factors (vertical bars) ─────────────────────────

    def generate_causes_bars(self, causes_data: Dict) -> io.BytesIO:
        """Vertical blue bars with % labels on top. Matches notebook chart."""
        logger.info("Chart 7: Causes bars...")

        counts      = causes_data.get('counts', {})
        percentages = causes_data.get('percentages', {})

        if not counts:
            counts      = {'Work flow\ndisruption': 38, 'Medication\nknowledge\nDeficiency': 29,
                           'Non\nadherence to\nguidelines': 20, 'Non\ncompetent\nemployee': 9,
                           'Non-treatment\nprotocol\ndeviation': 2, 'Monitoring': 2}
            percentages = counts

        items    = list(counts.items())[:6]
        labels   = [item[0] for item in items]
        values   = [percentages.get(lb, 0) for lb in labels]

        # Wrap long labels at 18 chars so they don't overlap
        wrapped_labels = ['\n'.join(textwrap.wrap(lb, width=18)) for lb in labels]

        fig, ax = plt.subplots(figsize=(13, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        x    = np.arange(len(labels))
        bars = ax.bar(x, values, width=0.55,
                      color=self.COLORS['blue'],
                      edgecolor='white', linewidth=1)

        # Labels on top
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.5,
                    f'{val:.0f}%', ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

        # Y-axis
        ax.set_ylim(0, max(values) * 1.25)
        ax.set_yticks(range(0, int(max(values) * 1.25) + 5, 5))
        ax.set_yticklabels([f'{y}%' for y in range(0, int(max(values) * 1.25) + 5, 5)])

        # X-axis — wrapped labels, extra bottom margin for multi-line
        ax.set_xticks(x)
        ax.set_xticklabels(wrapped_labels, fontsize=10, ha='center', linespacing=1.4)

        # Grid
        ax.grid(True, axis='y', linestyle='-', linewidth=0.8,
                color='#E0E0E0', alpha=0.7)
        ax.set_axisbelow(True)

        # Spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')

        ax.set_title('Contributing Factors', fontsize=13, fontweight='bold', pad=15)

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)
        return self._to_buf(fig)

    # ── save helper ──────────────────────────────────────────────────────────

    def save_chart(self, chart_name: str, buf: io.BytesIO) -> Path:
        output_path = self.output_dir / f"{chart_name}.png"
        data = buf.read() if hasattr(buf, 'read') else buf
        with open(output_path, 'wb') as f:
            f.write(data)
        logger.info(f"Saved: {output_path}")
        return output_path
