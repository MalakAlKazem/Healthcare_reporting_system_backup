"""
DOCX Report Generator for Healthcare Mortality System
=====================================================
Generates a multi-page Arabic RTL DOCX report with embedded Matplotlib charts.
Uses python-docx with raw XML manipulation for fine-grained control over
borders, shading, RTL layout, and cell merging.

Pages:
  1. Metadata table, results table, analysis box with chart1
  2. Building distribution (chart2), admission sources (chart3), age distribution (chart5)
  3. Age vs quarter (chart6), department pie (chart7) + data table, department analysis
  4. Department comparison (chart8), WHO age category (chart9)
  5. WHO diagnosis (chart10), doctor specialty table
  6. Final result, previous/current action tables, approval table
"""

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime
import os

from loguru import logger
from app.services.chart_generator import matplotlib_chart_generator

# =============================================================================
# FONTS
# =============================================================================
FONT = 'Traditional Arabic'           # Arabic body/table text
FONT_EN = 'Calibri'                   # English text (form numbers, values)
FONT_ANALYSIS = 'Frutiger LT Arabic 45 Light'  # Analysis text & chart subtitles

# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================
PAGE_WIDTH = Inches(8.27)             # A4 width
PAGE_HEIGHT = Inches(11.69)           # A4 height
MARGIN = Inches(0.7)                  # All margins
USABLE_WIDTH = Inches(6.87)           # PAGE_WIDTH - 2 * MARGIN

# =============================================================================
# BORDER PRESETS (sz is in eighths of a point: 4=0.5pt, 8=1pt, 12=1.5pt, 18=2.25pt)
# =============================================================================
BORDER_THICK = {'val': 'single', 'sz': '18', 'color': '000000', 'space': '0'}
BORDER_MEDIUM = {'val': 'single', 'sz': '12', 'color': '000000', 'space': '0'}
BORDER_THIN = {'val': 'single', 'sz': '8', 'color': '000000', 'space': '0'}
BORDER_FINE = {'val': 'single', 'sz': '4', 'color': '000000', 'space': '0'}
BORDER_NONE = {'val': 'none', 'sz': '0', 'color': 'FFFFFF', 'space': '0'}

# =============================================================================
# SHADING COLORS
# =============================================================================
SHADE_HEADER = 'EDEBE3'     # Gray — used for section headers (التحليل, النتيجة, etc.)
SHADE_TABLE = 'D9E2F3'      # Light blue — used for data table headers
SHADE_TOTAL = 'F2F2F2'      # Very light gray — used for total rows


class MatplotlibDocxGenerator:
    """
    Generates a mortality analysis DOCX report.

    Usage:
        generator = MatplotlibDocxGenerator()
        result = await generator.generate_report(data, history, options)
    """

    def __init__(self):
        self.logo_path = 'app/assets/LOGO.png'

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def generate_report(self, data, history=None, options=None):
        """
        Generate DOCX report with Matplotlib charts.

        Args:
            data: Statistics dictionary from the data service
            history: List of historical quarter data for trend charts
            options: Dict with 'quarter' and 'year' keys

        Returns:
            dict with 'filePath' and 'fileName'
        """
        options = options or {}
        quarter = options.get('quarter', 'الفصل الثالث')
        year = options.get('year', '2025')
        logger.info(f"Generating DOCX report for {quarter} {year}...")

        # Prepare current stats for chart generator
        stats = data.get('statistics', {})
        mortality_metrics = stats.get('mortality_metrics', {})
        current_stats = {
            'quarter': quarter,
            'year': year,
            'mortality_rate': mortality_metrics.get('rate', 0),
            'mortality_metrics': mortality_metrics,
            'rate': mortality_metrics.get('rate', 0),
            'total_deaths': stats.get('total_deaths', 0),
            'deaths': stats.get('total_deaths', 0),
            'kpi_deaths': stats.get('kpi_deaths', stats.get('total_deaths', 0)),
            'total_patients': stats.get('total_patients', 0),
            'buildings': stats.get('buildings', {}),
            'demographics': stats.get('demographics', {}),
            'clinical': stats.get('clinical', {}),
            'departments': stats.get('departments', []),
            'specialties': stats.get('specialties', []),
            'who_categories': data.get('who_categories', []),
            'who_categories_kpi': stats.get('who_categories_kpi', {})
        }

        # Generate all charts as BytesIO objects
        logger.info("Generating Matplotlib charts...")
        charts = matplotlib_chart_generator.generate_all_charts(current_stats, history or [])
        logger.info(f"Generated {len(charts)} charts")

        # Build the document
        doc = Document()
        section = doc.sections[0]
        self._setup_section(section)

        # Build all pages (pass stats + history to data-driven pages)
        self._build_page1(doc, quarter, year, current_stats, charts, history or [])
        self._build_page2(doc, charts, current_stats)
        self._build_page3(doc, charts, current_stats)
        self._build_page4(doc, charts, current_stats)
        self._build_page5(doc, charts, current_stats)
        self._build_last_page(doc)

        # Save to shared storage (accessible by Node backend)
        # __file__ is in python-service/app/services/ -> go up 3 levels to project root
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'storage', 'reports')
        reports_dir = os.path.normpath(reports_dir)
        os.makedirs(reports_dir, exist_ok=True)
        file_name = f'mortality-rate report {quarter} {year}.docx'
        file_path = os.path.join(reports_dir, file_name)
        doc.save(file_path)
        logger.success(f"DOCX report saved: {file_path}")

        return {'filePath': file_path, 'fileName': file_name}

    # =========================================================================
    # SECTION SETUP (page size, margins, borders, header, footer)
    # =========================================================================

    def _setup_section(self, section):
        """Configure page size, margins, page border, header and footer."""
        section.page_width = PAGE_WIDTH
        section.page_height = PAGE_HEIGHT
        section.top_margin = MARGIN
        section.bottom_margin = MARGIN
        section.left_margin = MARGIN
        section.right_margin = MARGIN

        # Page border (thin black line around each page)
        sectPr = section._sectPr
        pgBorders = OxmlElement('w:pgBorders')
        pgBorders.set(qn('w:offsetFrom'), 'page')
        for side in ('top', 'left', 'bottom', 'right'):
            border = OxmlElement(f'w:{side}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '12')
            border.set(qn('w:space'), '24')
            border.set(qn('w:color'), '000000')
            pgBorders.append(border)
        sectPr.append(pgBorders)

        self._add_header(section)
        self._add_footer(section)

    def _add_header(self, section):
        """Header: Logo (left) | Title (center) | Form number (right) + underline."""
        header = section.header
        for element in list(header._element):
            header._element.remove(element)

        # 3-column table for header layout
        table = header.add_table(rows=1, cols=3, width=Inches(7))
        self._set_table_cell_margins(table, top=0, bottom=0, left=0, right=0)
        cells = table.rows[0].cells
        cells[0].width = Inches(1.0)
        cells[1].width = Inches(5.0)
        cells[2].width = Inches(1.0)

        # Logo (left)
        if os.path.exists(self.logo_path):
            para = cells[0].paragraphs[0]
            para.add_run().add_picture(self.logo_path, width=Inches(0.5))
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            self._zero_spacing(para)

        # Title (center)
        para = cells[1].paragraphs[0]
        run = para.add_run("نموذج تحليل البيانات")
        run.font.name = FONT_ANALYSIS
        run.font.size = Pt(16)
        run.bold = True
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._set_rtl(para)
        self._zero_spacing(para)

        # Form number (right)
        para = cells[2].paragraphs[0]
        run = para.add_run('QS-36F-103(4)\nApd 15/12/2019')
        run.font.name = FONT_EN
        run.font.size = Pt(7)
        run.bold = True
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        self._zero_spacing(para)

        # Underline below header
        line_para = header.add_paragraph()
        line_para.paragraph_format.space_before = Pt(0)
        line_para.paragraph_format.space_after = Pt(8)
        line_para.paragraph_format.line_spacing = Pt(1)
        line_para.add_run("").font.size = Pt(1)

        pPr = line_para._element.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '8')
        bottom.set(qn('w:space'), '0')
        bottom.set(qn('w:color'), '000000')
        pBdr.append(bottom)
        pPr.append(pBdr)

    def _add_footer(self, section):
        """Footer: centered page number."""
        footer = section.footer
        for element in list(footer._element):
            footer._element.remove(element)

        para = footer.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()

        # PAGE field code
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        run._element.append(fldChar1)
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = 'PAGE'
        run._element.append(instrText)
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._element.append(fldChar2)

        run.font.size = Pt(10)
        run.font.name = FONT_EN

    # =========================================================================
    # PAGE 1: Metadata + Results + Analysis Box (with chart1)
    # =========================================================================

    def _build_page1(self, doc, quarter, year, stats, charts, history):
        """Page 1: metadata table, results table, analysis box with trend chart."""
        self._add_spacer(doc, space_before=6)
        self._add_metadata_table(doc, quarter, year)
        doc.add_paragraph()
        self._add_results_table(doc, stats, history)
        self._add_spacer(doc)
        self._add_analysis_box(doc, quarter, year, stats, charts)

    # =========================================================================
    # PAGE 2: Building distribution, Admission sources, Age distribution
    # =========================================================================

    def _build_page2(self, doc, charts, stats):
        """Page 2: chart2 (building), chart3 (admission), chart5 (age)."""
        doc.add_page_break()

        # Chart 2: Building Distribution (dynamic from stats['buildings'])
        if 'chart2' in charts:
            logger.info("Embedding Chart 2: Building Distribution...")
            self._add_rtl_para(doc, '- توزيع الوفيات بحسب المبنى', 9, bold=True, font=FONT_ANALYSIS)
            self._add_centered_chart(doc, charts['chart2'], width=4)

            buildings = stats.get('buildings', {})
            bci = buildings.get('bci', {})
            rah = buildings.get('rah', {})
            bci_pct = bci.get('percentage', 0)
            rah_pct = rah.get('percentage', 0)
            bci_rate = bci.get('rate', 0)
            rah_rate = rah.get('rate', 0)
            rah_deaths = rah.get('deaths', 0)

            # TODO: AI-generated — building comparison analysis
            building_text = (
                f"بالرغم من ان نسبة الوفيات في مركز القلب {bci_pct:.0f}% من اجمالي الوفيات ,الا انها كانت النسبة الاقل "
                f"مقارنة مع نسبة الوفيات في المبنى العام {rah_pct:.0f}% فقد شكلت {bci_rate:.1f}% من مرضى مركز القلب بينما شكلت "
                f"نسبة الوفيات في المبنى العام {rah_rate:.1f}%  من اجمالي المرضى في المبنى العام . و التي بلغت {rah_deaths} وفاة."
            )
            self._add_analysis_text(doc, building_text)
            logger.info("Chart 2 embedded")

        # Chart 3: Admission Sources
        if 'chart3' in charts:
            logger.info("Embedding Chart 3: Admission Sources...")
            self._add_rtl_para(doc, 'توزيع الوفيات بحسب وجهة الدخول', 9, bold=True, font=FONT_ANALYSIS)
            self._add_centered_chart(doc, charts['chart3'], width=5.5)
            logger.info("Chart 3 embedded")

        # Chart 5: Age Distribution
        if 'chart5' in charts:
            logger.info("Embedding Chart 5: Age Distribution...")
            self._add_rtl_para(doc, 'توزيع الوفيات بحسب عمر المتوفي', 9, bold=True, font=FONT_ANALYSIS)
            self._add_centered_chart(doc, charts['chart5'], width=5)
            logger.info("Chart 5 embedded")

    # =========================================================================
    # PAGE 3: Age vs Quarter, Department pie + table, Department analysis
    # =========================================================================

    def _build_page3(self, doc, charts, stats):
        """Page 3: chart6 (age by quarter), chart7 (dept pie) + data table, analysis text."""
        doc.add_page_break()

        # Chart 6: Age vs Quarter
        if 'chart6' in charts:
            logger.info("Embedding Chart 6: Age vs Quarter...")
            self._add_rtl_para(doc, 'مقارنة الوفيات بحسب العمر و الفصل', 11, bold=True, font=FONT_ANALYSIS)
            self._add_centered_chart(doc, charts['chart6'], width=6.5)

            # TODO: AI-generated — age vs quarter analysis
            age_text = (
                "بحسب الرسم البياني فإن عدد الوفيات ارتفع للاطفال الذين تراوحت اعمارهم اقل من 5 سنوات "
                "حيث ازداد العدد من 7 في الفصل الثاني الى 9 في الفصل الثالث .كما تجدر الاشارة الى ان عمر "
                "الاطفال التسعة تترواح من شهر او اقل من شهر. و تم تصنيفهم  7 congenital anomalies, 2 perinatal conditions"
            )
            self._add_analysis_text(doc, age_text)
            logger.info("Chart 6 embedded")

        # Chart 7: Department pie + side-by-side data table (dynamic)
        departments = stats.get('departments', [])
        if 'chart7' in charts:
            logger.info("Embedding Chart 7: Department Distribution...")
            self._add_rtl_para(doc, '- توزيع الوفيات بحسب الاقسام', 11, bold=True, font=FONT_ANALYSIS)
            self._add_dept_chart_with_table(doc, charts['chart7'], departments)

            # TODO: AI-generated — department analysis text
            total_deaths = stats.get('total_deaths', 0)
            dept_text = f"بلغ عدد الوفيات الاجمالي {total_deaths} حالة وفاة موزعة على الاقسام كما هو موضح في الرسم البياني اعلاه."
            self._add_analysis_text(doc, dept_text)
            logger.info("Chart 7 + table embedded")

    # =========================================================================
    # PAGE 4: Department comparison (chart8), WHO age category (chart9)
    # =========================================================================

    def _build_page4(self, doc, charts, stats):
        """Page 4: chart8 (dept comparison), chart9 (WHO age category)."""
        doc.add_page_break()

        # Chart 8: Department Comparison
        if 'chart8' in charts:
            logger.info("Embedding Chart 8: Department Comparison...")
            self._add_rtl_para(doc, 'مقارنة عدد الوفيات بحسب الاقسام', 11, bold=True, font=FONT_ANALYSIS)
            self._add_centered_chart(doc, charts['chart8'], width=6.5)

            # TODO: AI-generated — department comparison analysis
            chart8_text = (
                "يظهر لنا الرسم البياني اعلاه مقارنة عدد الوفيات بحسب الاقسام خلال الفصول المختلفة."
            )
            self._add_analysis_text(doc, chart8_text)
            logger.info("Chart 8 embedded")

        # Chart 9: WHO Age Category
        if 'chart9' in charts:
            logger.info("Embedding Chart 9: WHO Category Comparison...")
            self._add_rtl_para(doc, 'توزيع الوفيات بحسب التشخيص للسبب الذي نجم عنه الوفاة بحسب الفصل', 11, bold=True, font=FONT_ANALYSIS)
            self._add_centered_chart(doc, charts['chart9'], width=6.5)

            # TODO: AI-generated — WHO age category analysis
            chart9_text = (
                "يوضح الرسم البياني توزيع الوفيات بحسب الفئات العمرية وفق تصنيف منظمة الصحة العالمية."
            )
            self._add_analysis_text(doc, chart9_text)
            logger.info("Chart 9 embedded")

    # =========================================================================
    # PAGE 5: WHO Diagnosis chart + Doctor specialty table
    # =========================================================================

    def _build_page5(self, doc, charts, stats):
        """Page 5: chart10 (WHO diagnosis) + doctor specialty table."""
        doc.add_page_break()
        quarter = stats.get('quarter', '')
        specialties = stats.get('specialties', [])

        # Chart 10: WHO Diagnosis
        if 'chart10' in charts:
            logger.info("Embedding Chart 10: WHO Diagnosis...")
            self._add_rtl_para(doc, 'توزيع الوفيات بحسب التشخيص للسبب الذي نجم عنه الوفاة', 11, bold=True, font=FONT_ANALYSIS)

            # TODO: AI-generated — WHO diagnosis analysis
            who_text = (
                f"بناء لتصنيف منظمة الصحة العالمية WHO تم تصنيف ICD10 التابعة للوفيات في {quarter} "
                f"و كانت  النتيجة على الشكل التالي :"
            )
            self._add_analysis_text(doc, who_text)
            self._add_centered_chart(doc, charts['chart10'], width=6.5)
            logger.info("Chart 10 embedded")

        # Doctor specialty table (dynamic from stats)
        self._add_rtl_para(doc, 'توزيع الوفيات بحسب اختصاص الطبيب المعالج', 11, bold=True, font=FONT_ANALYSIS)
        self._add_doctor_specialty_table(doc, specialties)

    # =========================================================================
    # LAST PAGE: Final result, action tables, approval
    # =========================================================================

    def _build_last_page(self, doc):
        """Last page: final result, checkbox question, previous/current action tables, approval."""
        doc.add_page_break()
        self._add_spacer(doc, space_before=6)

        # --- النتيجة النهائية header ---
        self._add_titled_row(doc, "النتيجة النهائية", shade=SHADE_HEADER, border=BORDER_MEDIUM)

        # --- مشجعة value box ---
        self._add_titled_row(doc, "مشجعة", shade=None, border=BORDER_FINE)

        self._add_spacer(doc, space_before=6)

        # --- Checkbox question box ---
        self._add_checkbox_question_box(doc)

        self._add_spacer(doc, space_before=6)

        # --- Previous actions table ---
        self._add_previous_actions_table(doc)

        self._add_spacer(doc, space_before=6)

        # --- Current actions table ---
        self._add_current_actions_table(doc)

        # --- Instruction note ---
        p_title = doc.add_paragraph()
        self._set_rtl(p_title)
        p_title.paragraph_format.space_before = Pt(6)
        p_title.paragraph_format.space_after = Pt(4)
        p_title.paragraph_format.line_spacing = 1
        run_t = p_title.add_run('يجب ان تكون الاجراءات الواجب اتخاذها محددة وقابلة للقياس')
        run_t.font.name = FONT_ANALYSIS
        run_t.font.size = Pt(11)
        run_t.bold = True
        run_t.underline = True

        # --- Approval table ---
        self._add_approval_table(doc)

        # --- Final note ---
        p_note = doc.add_paragraph()
        self._set_rtl(p_note)
        p_note.paragraph_format.space_before = Pt(4)
        p_note.paragraph_format.space_after = Pt(0)
        p_note.paragraph_format.line_spacing = 1
        run_note = p_note.add_run(
            'يجب توقيع جميع المعنيين بمتابعة الاجراءات المتخذة او من ينوب عنهم في خانة الموافقة اضافة الى مدراء الادارات المعنيين'
        )
        run_note.font.name = FONT_ANALYSIS
        run_note.font.size = Pt(11)
        run_note.bold = True

    # =========================================================================
    # PAGE 1 COMPONENTS
    # =========================================================================

    def _add_metadata_table(self, doc, quarter, year):
        """
        3-row x 4-column metadata table with merged cells and custom borders.
        Columns (RTL): rightLabel | rightValue | midLabel | leftValue
        Cols 2+3 have rows 0+1 vertically merged.
        """
        table = doc.add_table(rows=3, cols=4)
        table.autofit = False
        self._set_table_cell_margins(table, top=0, bottom=0, left=60, right=60)

        # Column widths (total = 6.87")
        col_w = [Inches(1.93), Inches(1.06), Inches(2.71), Inches(1.17)]
        for i, width in enumerate(col_w):
            for row in table.rows:
                row.cells[i].width = width

        # --- Row 0 ---
        self._style_cell_text(table.cell(0, 3), "موضوع التحليل", FONT, 10, bold=True, rtl=True)
        self._set_cell_shading(table.cell(0, 3), SHADE_HEADER)
        self._style_cell_text(table.cell(0, 2), "Inpatient Mortality rate", FONT_EN, 11, bold=True)
        self._style_cell_text(table.cell(0, 1), "الإدارة", FONT, 10, bold=True, rtl=True)
        self._set_cell_shading(table.cell(0, 1), SHADE_HEADER)
        self._style_cell_text(table.cell(0, 0), "الطبية", FONT, 11, rtl=True)

        # --- Row 1 ---
        self._style_cell_text(table.cell(1, 3), "", FONT, 9, rtl=True)
        self._set_cell_shading(table.cell(1, 3), SHADE_HEADER)
        self._style_cell_text(table.cell(1, 2), "", FONT_EN, 10)
        self._style_cell_text(table.cell(1, 1), "الوحدة الإدارية", FONT, 10, bold=True, rtl=True)
        self._set_cell_shading(table.cell(1, 1), SHADE_HEADER)
        self._style_cell_text(table.cell(1, 0), "....................", FONT, 10, rtl=True)

        # --- Row 2 ---
        self._style_cell_text(table.cell(2, 3), "مصادر\nالبيانات\n)تحديد اسماء\nالنماذج(", FONT, 9, bold=True, rtl=True)
        self._set_cell_shading(table.cell(2, 3), SHADE_HEADER)
        self._style_cell_text(table.cell(2, 2), "سجل الوفيات", FONT, 11, rtl=True)
        self._style_cell_text(table.cell(2, 1), "الشهر / العام\nأو\nالفصل / العام", FONT, 9, bold=True, rtl=True)
        self._set_cell_shading(table.cell(2, 1), SHADE_HEADER)
        self._style_cell_text(table.cell(2, 0), f"{quarter} {year}", FONT, 11, rtl=True)

        # Vertical merges (cols 2 & 3: rows 0+1)
        table.cell(0, 2).merge(table.cell(1, 2))
        table.cell(0, 3).merge(table.cell(1, 3))
        self._set_cell_shading(table.cell(0, 3), SHADE_HEADER)

        # --- Borders (must handle merged cells via raw XML) ---
        row0_tcs = table.rows[0]._tr.findall(qn('w:tc'))
        row1_tcs = table.rows[1]._tr.findall(qn('w:tc'))

        # Col 0: 3 separate rows
        self._set_cell_border(table.cell(0, 0), top=BORDER_THICK, bottom=BORDER_THIN, left=BORDER_THICK, right=BORDER_THIN)
        self._set_cell_border(table.cell(1, 0), top=BORDER_THIN, bottom=BORDER_THIN, left=BORDER_THICK, right=BORDER_THIN)
        self._set_cell_border(table.cell(2, 0), top=BORDER_THIN, bottom=BORDER_THICK, left=BORDER_THICK, right=BORDER_THIN)

        # Col 1: 3 separate rows, thick right border (separator)
        self._set_cell_border(table.cell(0, 1), top=BORDER_THICK, bottom=BORDER_THIN, left=BORDER_THIN, right=BORDER_THICK)
        self._set_cell_border(table.cell(1, 1), top=BORDER_THIN, bottom=BORDER_THIN, left=BORDER_THIN, right=BORDER_THICK)
        self._set_cell_border(table.cell(2, 1), top=BORDER_THIN, bottom=BORDER_THICK, left=BORDER_THIN, right=BORDER_THICK)

        # Col 2: rows 0+1 merged — set borders on raw tc elements
        self._set_tc_border(row0_tcs[2], top=BORDER_THICK, bottom=BORDER_THIN, left=BORDER_THICK, right=BORDER_THIN)
        self._set_tc_border(row1_tcs[2], top=BORDER_THIN, bottom=BORDER_THIN, left=BORDER_THICK, right=BORDER_THIN)
        self._set_cell_border(table.cell(2, 2), top=BORDER_THIN, bottom=BORDER_THICK, left=BORDER_THICK, right=BORDER_THIN)

        # Col 3: rows 0+1 merged
        self._set_tc_border(row0_tcs[3], top=BORDER_THICK, bottom=BORDER_THIN, left=BORDER_THIN, right=BORDER_THICK)
        self._set_tc_border(row1_tcs[3], top=BORDER_THIN, bottom=BORDER_THIN, left=BORDER_THIN, right=BORDER_THICK)
        self._set_cell_border(table.cell(2, 3), top=BORDER_THIN, bottom=BORDER_THICK, left=BORDER_THIN, right=BORDER_THICK)

    def _add_results_table(self, doc, stats, history):
        """
        4-row x 6-column results table with dynamic history.
        Row 0: merged title 'النتائج'
        Row 1: instruction (merged 5 cols) + 'النتيجة الحالية'
        Row 2: 5 quarter headers from history
        Row 3: 5 historical rates + current rate
        """
        table = doc.add_table(rows=4, cols=6)
        table.autofit = False
        self._set_table_cell_margins(table, top=40, bottom=40, left=60, right=60)

        # Equal column widths
        w_col = Inches(6.87 / 6)
        for i in range(6):
            for row in table.rows:
                row.cells[i].width = w_col

        # Row 0: title
        cell0 = table.cell(0, 0)
        for c in range(1, 6):
            cell0 = cell0.merge(table.cell(0, c))
        self._style_cell_text(table.cell(0, 0), "النتائج", FONT, 11, bold=True, rtl=True)
        self._set_cell_shading(table.cell(0, 0), SHADE_HEADER)

        # Row 1: instruction + current result label
        instr = table.cell(1, 0)
        for c in range(1, 5):
            instr = instr.merge(table.cell(1, c))
        self._style_cell_text(
            table.cell(1, 0),
            "في حال كان هناك نتائج سابقة عن الموضوع الذي يتم تحليله يجب ذكره مع تحديد الفترة:\nالشهر / الفصل / العام",
            FONT, 10, rtl=True
        )
        self._set_cell_shading(table.cell(1, 0), SHADE_HEADER)
        self._style_cell_text(table.cell(1, 5), "النتيجة الحالية", FONT, 11, bold=True, rtl=True)
        self._set_cell_shading(table.cell(1, 5), SHADE_HEADER)

        # Row 2: quarter headers — last 5 history entries, oldest at col 0, newest at col 4
        # history is oldest-first; history[-5:] gives the 5 most recent
        last5 = history[-5:] if len(history) >= 5 else history
        # Pad left with empty entries if fewer than 5
        while len(last5) < 5:
            last5 = [{}] + last5
        for i in range(5):
            entry = last5[i]
            label = f"{entry['quarter']} {entry['year']}" if entry.get('quarter') else ""
            self._style_cell_text(table.cell(2, i), label, FONT, 10, rtl=True)
            self._set_cell_shading(table.cell(2, i), SHADE_HEADER)
        self._style_cell_text(table.cell(2, 5), "", FONT, 10, rtl=True)
        self._set_cell_shading(table.cell(2, 5), SHADE_HEADER)

        # Row 3: historical rates + current rate
        for i in range(5):
            entry = last5[i]
            val = f"{entry['rate']:.2f}%" if entry.get('rate') else ""
            self._style_cell_text(table.cell(3, i), val, FONT_EN, 11)

        current_rate = stats.get('mortality_rate', 0)
        try:
            curr = float(current_rate)
        except Exception:
            curr = 0.0
        self._style_cell_text(table.cell(3, 5), f"%{curr:.2f}", FONT, 11, bold=True, rtl=True)

        # Borders: thin everywhere, thick on outer edges
        for row in table.rows:
            for cell in row.cells:
                self._set_cell_border(cell, top=BORDER_THIN, bottom=BORDER_THIN, left=BORDER_THIN, right=BORDER_THIN)
        for c in range(6):
            self._set_cell_border(table.cell(0, c), top=BORDER_THICK, left=BORDER_THIN, right=BORDER_THIN, bottom=BORDER_THIN)
            self._set_cell_border(table.cell(3, c), bottom=BORDER_THICK, left=BORDER_THIN, right=BORDER_THIN, top=BORDER_THIN)
        for r in range(4):
            self._set_cell_border(table.cell(r, 0), left=BORDER_THICK, top=BORDER_THIN, right=BORDER_THIN, bottom=BORDER_THIN)
            self._set_cell_border(table.cell(r, 5), right=BORDER_THICK, top=BORDER_THIN, left=BORDER_THIN, bottom=BORDER_THIN)

    def _add_analysis_box(self, doc, quarter, year, stats, charts):
        """
        Bordered container box on page 1 containing:
        - *التحليل header with gray background
        - Analysis text with bold subtitle (dynamic rate from stats)
        - Chart 1 (mortality trend)
        """
        mortality_rate = stats.get('mortality_rate', 0)

        # Container: 1-cell table with thick border
        box = doc.add_table(rows=1, cols=1)
        box.autofit = False
        para_before = doc.paragraphs[-2]
        para_before.paragraph_format.space_before = Pt(0)
        para_before.paragraph_format.space_after = Pt(0)
        box.columns[0].width = USABLE_WIDTH
        cell = box.cell(0, 0)
        self._zero_spacing(cell.paragraphs[0])
        self._set_table_cell_margins(box, top=0, bottom=10, left=20, right=20)
        self._set_cell_border(cell, top=BORDER_MEDIUM, bottom=BORDER_MEDIUM, left=BORDER_MEDIUM, right=BORDER_MEDIUM)

        # Remove default empty paragraph
        cell.text = ""
        for paragraph in cell.paragraphs:
            paragraph._element.getparent().remove(paragraph._element)

        # --- Header row: *التحليل ---
        title_tbl = cell.add_table(rows=1, cols=1)
        title_tbl.autofit = False
        title_tbl.columns[0].width = Inches(9)
        title_cell = title_tbl.cell(0, 0)
        self._set_table_cell_margins(title_tbl, top=0, bottom=0, left=20, right=20)
        self._set_cell_shading(title_cell, SHADE_HEADER)
        self._set_cell_border(title_cell, bottom=BORDER_MEDIUM)
        self._style_cell_text(title_cell, "*التحليل", FONT, 11, bold=True, rtl=True)

        # Remove auto-inserted paragraph after title table
        for p_after in cell.paragraphs:
            p_after._element.getparent().remove(p_after._element)

        # --- Analysis text (dynamic from stats) ---
        p2 = cell.add_paragraph()
        self._set_rtl(p2)
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        self._zero_spacing(p2)

        run1 = p2.add_run(
            f"هذا التحليل يتضمن عدد الوفيات في {quarter} من العام {year}، وتم احتساب نسبة "
            f"الوفيات للمرضى الذين مكثوا في المستشفى أكثر من 24 ساعة.\n"
        )
        run1.font.name = FONT_ANALYSIS
        run1.font.size = Pt(11)

        run_subtitle = p2.add_run("مقارنة نسبة الوفيات مع Target:\n")
        run_subtitle.font.name = FONT_ANALYSIS
        run_subtitle.font.size = Pt(11)
        run_subtitle.bold = True

        # TODO: AI-generated — this paragraph should be generated by AI model
        run3 = p2.add_run(
            f"بلغت نسبة الوفيات في {quarter} من العام {year}: {mortality_rate:.2f}%.\n"
            f"تمت مقارنة النتيجة مع الفصول السابقة كما في الشكل التالي:"
        )
        run3.font.name = FONT_ANALYSIS
        run3.font.size = Pt(11)

        # --- Chart 1: Mortality Trend ---
        if 'chart1' in charts:
            p3 = cell.add_paragraph()
            run = p3.add_run("Inpatient mortality rate\nT<2%")
            run.font.name = FONT_EN
            run.font.size = Pt(11)
            run.bold = True
            p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p3.paragraph_format.space_before = Pt(0)
            p3.paragraph_format.space_after = Pt(4)

            pimg = cell.add_paragraph()
            pimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pimg.add_run().add_picture(charts['chart1'], width=Inches(6.8))
            pimg.paragraph_format.space_before = Pt(0)
            pimg.paragraph_format.space_after = Pt(2)

        # Compress all paragraphs inside box
        for p in cell.paragraphs:
            self._zero_spacing(p)

    # =========================================================================
    # PAGE 3 COMPONENTS
    # =========================================================================

    def _add_dept_chart_with_table(self, doc, chart7, departments):
        """Chart 7 (pie) on the right + department data table on the left (RTL layout)."""
        # Layout table: 2 columns, no borders
        layout_tbl = doc.add_table(rows=1, cols=2)
        layout_tbl.autofit = False
        for cell in layout_tbl.rows[0].cells:
            self._set_cell_border(cell, top=BORDER_NONE, bottom=BORDER_NONE, left=BORDER_NONE, right=BORDER_NONE)

        # Column widths (RTL: col0=left=table, col1=right=chart)
        layout_tbl.rows[0].cells[0].width = Inches(2.67)
        layout_tbl.rows[0].cells[1].width = Inches(4.2)

        # Chart cell (right in RTL = index 1)
        chart_cell = layout_tbl.rows[0].cells[1]
        chart_p = chart_cell.paragraphs[0]
        chart_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._zero_spacing(chart_p)
        chart_p.add_run().add_picture(chart7, width=Inches(4))

        # Data table cell (left in RTL = index 0)
        data_cell = layout_tbl.rows[0].cells[0]

        # Add margins so nested table border is visible
        tcPr = data_cell._element.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for edge, val in [('w:right', '80'), ('w:left', '80')]:
            m = OxmlElement(edge)
            m.set(qn('w:w'), val)
            m.set(qn('w:type'), 'dxa')
            tcMar.append(m)
        tcPr.append(tcMar)

        # Remove default paragraph
        for p in data_cell.paragraphs:
            p._element.getparent().remove(p._element)

        # Build department data dynamically from stats
        dept_display_names = {
            'c2': 'Cardiac 2',
        }
        total_count = sum(d.get('count', 0) for d in departments)
        dept_data = [('النسبة', 'عدد الوفيات', 'القسم')]
        for dept in departments:
            pct = f"{dept.get('percentage', 0):.0f}%"
            count = str(dept.get('count', 0))
            name = dept.get('name', '')
            name = dept_display_names.get(name.lower().strip(), name)
            dept_data.append((pct, count, name))
        dept_data.append(('100%', str(total_count), 'المجموع'))

        num_rows = len(dept_data)
        dept_table = data_cell.add_table(rows=num_rows, cols=3)
        dept_table.autofit = False
        self._set_table_cell_margins(dept_table, top=20, bottom=20, left=40, right=40)

        last_row = num_rows - 1
        for i, (col1, col2, col3) in enumerate(dept_data):
            row_cells = dept_table.rows[i].cells
            for j, val in enumerate([col1, col2, col3]):
                is_arabic = any('\u0600' <= c <= '\u06FF' for c in val)
                font = FONT if is_arabic else FONT_EN
                self._style_cell_text(row_cells[j], val, font, 11, bold=(i == 0 or i == last_row), rtl=is_arabic, align='center')
                self._set_cell_border(row_cells[j], top=BORDER_FINE, bottom=BORDER_FINE, left=BORDER_FINE, right=BORDER_FINE)

            if i == 0:
                self._shade_row_cells(row_cells, SHADE_TABLE)
            elif i == last_row:
                self._shade_row_cells(row_cells, SHADE_TOTAL)

        # Column widths
        for row in dept_table.rows:
            for j, w in enumerate([Inches(0.7), Inches(0.87), Inches(1.0)]):
                row.cells[j].width = w

    # =========================================================================
    # PAGE 5 COMPONENTS
    # =========================================================================

    def _add_doctor_specialty_table(self, doc, specialties):
        """Dynamic doctor specialty table: 3 columns (specialty, count, percentage)."""
        # Build rows: header + data + total
        total_count = sum(s.get('count', 0) for s in specialties)
        doctor_data = [('اختصاص الطبيب', 'العدد', 'النسبة')]
        for spec in specialties:
            name = spec.get('name', '')
            count = str(spec.get('count', 0))
            pct = f"{spec.get('percentage', 0):.1f}%"
            doctor_data.append((name, count, pct))
        doctor_data.append(('المجموع', str(total_count), '100%'))

        num_rows = len(doctor_data)
        table = doc.add_table(rows=num_rows, cols=3)
        table.autofit = False
        self._set_table_cell_margins(table, top=20, bottom=20, left=40, right=40)
        self._set_table_rtl(table)

        last_row = num_rows - 1
        for i, (col1, col2, col3) in enumerate(doctor_data):
            row_cells = table.rows[i].cells
            for j, val in enumerate([col1, col2, col3]):
                is_arabic = any('\u0600' <= c <= '\u06FF' for c in val)
                font = FONT if is_arabic else FONT_EN
                self._style_cell_text(row_cells[j], val, font, 11, bold=(i == 0 or i == last_row), rtl=True, align='center')
                self._set_cell_border(row_cells[j], top=BORDER_FINE, bottom=BORDER_FINE, left=BORDER_FINE, right=BORDER_FINE)

            if i == 0:
                self._shade_row_cells(row_cells, SHADE_TABLE)
            elif i == last_row:
                self._shade_row_cells(row_cells, SHADE_TOTAL)

        # Column widths
        for row in table.rows:
            row.cells[0].width = Inches(3.5)
            row.cells[1].width = Inches(1.0)
            row.cells[2].width = Inches(1.0)

    # =========================================================================
    # LAST PAGE COMPONENTS
    # =========================================================================

    def _add_checkbox_question_box(self, doc):
        """Bordered box with checkbox question about previous improvement actions."""
        box_tbl = doc.add_table(rows=1, cols=1)
        box_tbl.autofit = False
        box_tbl.columns[0].width = USABLE_WIDTH
        self._set_table_cell_margins(box_tbl, top=30, bottom=30, left=60, right=60)

        cell = box_tbl.cell(0, 0)
        self._set_cell_border(cell, top=BORDER_FINE, bottom=BORDER_FINE, left=BORDER_FINE, right=BORDER_FINE)

        # Line 1: question with checkboxes
        p = cell.paragraphs[0]
        self._set_rtl(p)
        self._zero_spacing(p)

        self._add_run(p, 'هل تم اتخاذ اجراءات تحسينية سابقا حول موضوع التحليل :      ', FONT_ANALYSIS, 11)
        self._add_run(p, 'نعم', FONT_ANALYSIS, 11)
        self._add_run(p, ' ☐', None, 11)
        self._add_run(p, '         ', None, 11)
        self._add_run(p, 'كلا  ', FONT_ANALYSIS, 11)
        self._add_run(p, ' ☐ ', None, 11)

        # Line 2: instruction
        p2 = cell.add_paragraph()
        self._set_rtl(p2)
        self._zero_spacing(p2)
        self._add_run(p2,
            'في حال نعم , يجب تعبئة جدول " الاجراءات المتخذة سابقا" و في حال كلا , الانتقال الى جدول "الاجراءات المتخذة الحالية"',
            FONT_ANALYSIS, 11
        )

    def _add_previous_actions_table(self, doc):
        """5-column table for previous corrective actions."""
        table = doc.add_table(rows=3, cols=5)
        table.autofit = False
        self._set_table_cell_margins(table, top=20, bottom=20, left=40, right=40)
        self._set_table_rtl(table)

        # Row 0: merged title
        table.cell(0, 0).merge(table.cell(0, 4))
        self._style_cell_text(table.cell(0, 0), 'الاجراءات المتخذة  السابقة', FONT, 10, bold=True, rtl=True, align='center')

        # Row 1: headers
        headers = ['الرقم', 'الاجراءات المقترحة سابقا', 'التاريخ المتوقع لتنفيذ الاجراء',
                   'تم التنفيذ )نعم/كلا(', 'في حال كلا ) الاجراءات التصحيحية الجديدة(']
        for j, h in enumerate(headers):
            self._style_cell_text(table.cell(1, j), h, FONT, 11, bold=True, rtl=True, align='center')

        # Row 2: empty data + last column with checkbox options
        for j in range(4):
            table.cell(2, j).text = ''

        last_cell = table.cell(2, 4)
        last_cell.text = ''
        p1 = last_cell.paragraphs[0]
        self._add_run(p1, ' ☐  الغاء الاجراء', FONT, 11)
        self._zero_spacing(p1)
        self._set_rtl(p1)
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p2 = last_cell.add_paragraph()
        self._add_run(p2, ' ☐ اضافة الاجراء ضمن الاجراءات المتخذة الحالية.)الجدول ادناه(', FONT, 11)
        self._zero_spacing(p2)
        self._set_rtl(p2)
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Shading rows 0-1, borders all
        for i in range(2):
            self._shade_row_cells(table.rows[i].cells, SHADE_HEADER)
        self._apply_borders_to_table(table, BORDER_FINE)

        # Column widths
        widths = [Inches(0.5), Inches(1.8), Inches(1.37), Inches(1.1), Inches(2.1)]
        for row in table.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = w

    def _add_current_actions_table(self, doc):
        """4-column table for current corrective actions (4 empty data rows)."""
        table = doc.add_table(rows=6, cols=4)
        table.autofit = False
        self._set_table_cell_margins(table, top=20, bottom=20, left=40, right=40)
        self._set_table_rtl(table)

        # Row 0: merged title
        table.cell(0, 0).merge(table.cell(0, 3))
        self._style_cell_text(table.cell(0, 0), 'الاجراءات المتخذة  الحالية', FONT, 10, bold=True, rtl=True, align='center')

        # Row 1: headers
        headers = ['الرقم', 'الاجراءات الواجب اتخاذها لحل الموضوع', 'الشخص المعني بالمتابعة', 'التاريخ المتوقع للتنفيذ']
        for j, h in enumerate(headers):
            self._style_cell_text(table.cell(1, j), h, FONT, 11, bold=True, rtl=True, align='center')

        # Rows 2-5: empty
        for i in range(2, 6):
            for j in range(4):
                table.cell(i, j).text = ''

        # Shading rows 0-1, borders all
        for i in range(2):
            self._shade_row_cells(table.rows[i].cells, SHADE_HEADER)
        self._apply_borders_to_table(table, BORDER_FINE)

        # Column widths
        widths = [Inches(0.5), Inches(3.07), Inches(1.8), Inches(1.5)]
        for row in table.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = w

    def _add_approval_table(self, doc):
        """
        4-row x 5-column approval table.
        Row 0: empty | اعداد | موافقة (merged 3 cols)
        Rows 1-3: الاسم/التوقيع/التاريخ labels + empty cells
        """
        table = doc.add_table(rows=4, cols=5)
        table.autofit = False
        self._set_table_cell_margins(table, top=20, bottom=20, left=40, right=40)
        self._set_table_rtl(table)

        # Row 0 header
        table.cell(0, 0).text = ''
        self._style_cell_text(table.cell(0, 1), 'اعداد', FONT, 11, bold=True, rtl=True, align='center')
        table.cell(0, 2).merge(table.cell(0, 4))
        self._style_cell_text(table.cell(0, 2), 'موافقة', FONT, 11, bold=True, rtl=True, align='center')

        # Rows 1-3: labels
        for i, label in enumerate(['الاسم', 'التوقيع', 'التاريخ']):
            self._style_cell_text(table.cell(i + 1, 0), label, FONT, 11, bold=True, rtl=True, align='center')
            for j in range(1, 5):
                table.cell(i + 1, j).text = ''

        # Shading + borders
        self._shade_row_cells(table.rows[0].cells, SHADE_HEADER)
        self._apply_borders_to_table(table, BORDER_FINE)

        # Column widths
        widths = [Inches(0.8), Inches(1.5), Inches(1.52), Inches(1.52), Inches(1.53)]
        for row in table.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = w

    # =========================================================================
    # REUSABLE HELPER METHODS
    # =========================================================================

    def _add_spacer(self, doc, space_before=0):
        """Add an invisible spacer paragraph."""
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(space_before)
        sp.paragraph_format.space_after = Pt(0)
        sp.paragraph_format.line_spacing = Pt(1)
        sp.add_run("").font.size = Pt(1)

    def _add_centered_chart(self, doc, chart_bytes, width=6.5):
        """Add a chart image centered in a new paragraph."""
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._zero_spacing(para)
        para.add_run().add_picture(chart_bytes, width=Inches(width))

    def _add_analysis_text(self, doc, text):
        """Add an RTL analysis text paragraph with FONT_ANALYSIS at 11pt."""
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.font.name = FONT_ANALYSIS
        run.font.size = Pt(11)
        self._set_rtl(para)
        self._zero_spacing(para)

    def _add_titled_row(self, doc, text, shade=None, border=BORDER_FINE):
        """Add a single-cell table row used as a section header or value box."""
        tbl = doc.add_table(rows=1, cols=1)
        tbl.autofit = False
        tbl.columns[0].width = USABLE_WIDTH
        self._set_table_cell_margins(tbl, top=0 if shade else 20, bottom=0 if shade else 20, left=20, right=20)
        cell = tbl.cell(0, 0)
        if shade:
            self._set_cell_shading(cell, shade)
        self._set_cell_border(cell, top=border, bottom=border, left=border, right=border)
        self._style_cell_text(cell, text, FONT, 11, bold=True, rtl=True, align='center')

    def _add_rtl_para(self, doc, text, size, bold=False, font=None):
        """Add an RTL paragraph with specified font, size, and bold."""
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.font.name = font or FONT
        run.font.size = Pt(size)
        run.bold = bold
        self._set_rtl(para)
        self._zero_spacing(para)

    def _add_run(self, para, text, font_name, size, bold=False):
        """Add a styled run to an existing paragraph."""
        run = para.add_run(text)
        if font_name:
            run.font.name = font_name
        run.font.size = Pt(size)
        run.bold = bold
        return run

    def _zero_spacing(self, para):
        """Remove all spacing from a paragraph."""
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = 1

    def _set_rtl(self, para):
        """Set paragraph direction to RTL."""
        para.paragraph_format.right_to_left = True
        pPr = para._element.get_or_add_pPr()
        bidi = OxmlElement('w:bidi')
        bidi.set(qn('w:val'), '1')
        pPr.append(bidi)

    def _set_table_rtl(self, table):
        """Set entire table to RTL visual layout."""
        bidi = OxmlElement('w:bidiVisual')
        bidi.set(qn('w:val'), '1')
        table._tbl.tblPr.append(bidi)

    def _shade_row_cells(self, cells, color):
        """Apply shading to all cells in a row."""
        for cell in cells:
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), color)
            shading.set(qn('w:val'), 'clear')
            cell._element.get_or_add_tcPr().append(shading)

    def _apply_borders_to_table(self, table, border_style):
        """Apply the same border style to every cell in a table."""
        for row in table.rows:
            for cell in row.cells:
                self._set_cell_border(cell, top=border_style, bottom=border_style, left=border_style, right=border_style)

    # =========================================================================
    # LOW-LEVEL XML HELPERS
    # =========================================================================

    def _set_table_cell_margins(self, table, top=50, bottom=50, left=80, right=80):
        """Set cell margins for an entire table (in twips/dxa)."""
        tblCellMar = OxmlElement('w:tblCellMar')
        for side, val in (('top', top), ('bottom', bottom), ('left', left), ('right', right)):
            node = OxmlElement(f'w:{side}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tblCellMar.append(node)
        table._tbl.tblPr.append(tblCellMar)

    def _set_cell_shading(self, cell, fill_hex):
        """Fill a table cell with a background color."""
        tcPr = cell._element.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill_hex)
        tcPr.append(shd)

    def _set_cell_border(self, cell, **kwargs):
        """
        Set borders on a python-docx cell object.
        Args: top, left, bottom, right — each a dict like BORDER_THIN.
        """
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        tcBorders = tcPr.first_child_found_in('w:tcBorders')
        if tcBorders is None:
            tcBorders = OxmlElement('w:tcBorders')
            tcPr.append(tcBorders)

        for edge in ('top', 'left', 'bottom', 'right'):
            if edge in kwargs:
                tag = f'w:{edge}'
                element = tcBorders.find(qn(tag))
                if element is None:
                    element = OxmlElement(tag)
                    tcBorders.append(element)
                for k, v in kwargs[edge].items():
                    element.set(qn('w:' + k), str(v))

    def _set_tc_border(self, tc, **kwargs):
        """
        Set borders on a raw <w:tc> XML element.
        Needed for vMerge continuation cells where python-docx cell access doesn't work.
        """
        tcPr = tc.get_or_add_tcPr()
        tcBorders = tcPr.first_child_found_in('w:tcBorders')
        if tcBorders is None:
            tcBorders = OxmlElement('w:tcBorders')
            tcPr.append(tcBorders)

        for edge in ('top', 'left', 'bottom', 'right'):
            if edge in kwargs:
                tag = f'w:{edge}'
                element = tcBorders.find(qn(tag))
                if element is None:
                    element = OxmlElement(tag)
                    tcBorders.append(element)
                for k, v in kwargs[edge].items():
                    element.set(qn('w:' + k), str(v))

    def _style_cell_text(self, cell, text, font_name, font_size, bold=False, rtl=False, align='center'):
        """Write styled text into a table cell."""
        cell.text = ''
        p = cell.paragraphs[0]
        r = p.add_run(text)
        r.font.name = font_name
        r.font.size = Pt(font_size)
        r.bold = bold
        self._zero_spacing(p)

        if align == 'center':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == 'right':
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if rtl:
            self._set_rtl(p)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
matplotlib_docx_generator = MatplotlibDocxGenerator()
