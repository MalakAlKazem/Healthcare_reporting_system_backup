"""
AI Analysis Service — Qwen2.5 Local Inference
==============================================
Generates Arabic medical analysis paragraphs for the mortality report.

FIXES IN THIS VERSION:
  FIX-1  : analyze_mortality_trend — added target_rate param + vs_target sentence
  FIX-2  : analyze_mortality_trend — forbidden phrase list stops "المبلغ عنه"
  FIX-3  : analyze_building_distribution — always includes both patient-rate AND pct
  FIX-4  : analyze_dept_comparison — removed growth-% from prompt (was misleading)
  FIX-5  : analyze_departments — each dept listed individually with exact name+count+%
  FIX-6  : analyze_who_comparison / analyze_who_diagnosis — kept for API compat,
            but main WHO text is now built statically in docx_generator (no hallucination)
"""

import os
import multiprocessing
from loguru import logger

MODEL_PATH = os.environ.get(
    'QWEN_MODEL_PATH',
    'C:/models/qwen2.5-7b-instruct-q3_k_m.gguf'
)

SYSTEM_PROMPT = (
    "أنت محلل بيانات طبي خبير في تقارير الوفيات للمستشفيات. "
    "اكتب تحليلاً احترافياً باللغة العربية الفصحى.\n"
    "القواعد الأساسية:\n"
    "1. استخدم اللغة العربية الفصحى السليمة مع علامات الترقيم المناسبة\n"
    "2. اكتب فقرة واحدة متماسكة ومتصلة (3-5 جمل)\n"
    "3. لا تستخدم النقاط أو التعداد الرقمي داخل الفقرة\n"
    "4. ابدأ مباشرة بالتحليل بدون مقدمات\n"
    "5. استخدم الأرقام كما هي في البيانات فقط، لا تخترع أرقاماً\n"
    "6. ممنوع استخدام عبارة 'المبلغ عنه' أو 'وفقاً للبيانات' أو 'بناءً على'\n"
    "7. استخدم الأقواس الصحيحة هكذا: (مثال) وليس )مثال(\n"
    "8. لا تذكر نسب مئوية للنمو أو الارتفاع — فقط الأرقام المطلقة\n"
    "9. لا تخترع أسماء أمراض أو أقسام غير موجودة في البيانات"
)


class AIAnalysisService:

    def __init__(self):
        self._llm = None

    def _load_model(self):
        if self._llm is not None:
            return True
        try:
            from llama_cpp import Llama
        except ImportError:
            logger.warning("llama-cpp-python not installed.")
            return False
        if not os.path.exists(MODEL_PATH):
            logger.warning(f"Model file not found: {MODEL_PATH}")
            return False
        try:
            logger.info(f"Loading Qwen2.5 model from {MODEL_PATH} ...")
            n_threads = min(8, multiprocessing.cpu_count())
            self._llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=1024,
                n_threads=n_threads,
                n_batch=512,
                verbose=False
            )
            logger.success("Qwen2.5 model loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def _generate(self, user_prompt, max_tokens=150):
        if not self._load_model():
            return ""
        try:
            result = self._llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1,
                repeat_penalty=1.1,
                stop=["###", "---", "\n\n\n"]
            )
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""

    def _is_valid_arabic_output(self, text):
        if not text or len(text.strip()) < 20:
            return False
        cjk = sum(1 for c in text
                  if '\u4e00' <= c <= '\u9fff'
                  or '\u3040' <= c <= '\u30ff'
                  or '\u3400' <= c <= '\u4dbf'
                  or '\uf900' <= c <= '\ufaff')
        if cjk > 0:
            logger.warning(f"AI output rejected: {cjk} CJK chars → fallback")
            return False
        return True

    def _safe_generate(self, user_prompt, max_tokens=150):
        text = self._generate(user_prompt, max_tokens)
        return text if self._is_valid_arabic_output(text) else ""

    # =========================================================================
    # METHOD 1 — Page 1: Mortality Trend
    # FIX-1: added target_rate param + explicit vs_target line
    # FIX-2: forbidden phrases added to prompt
    # =========================================================================

    def analyze_mortality_trend(
        self, quarter, year, current_rate, current_deaths,
        prev_rate, prev_deaths, prev_quarter,
        target_rate=2.0
    ):
        trend     = "ارتفاع" if current_rate > prev_rate else "انخفاض"
        diff      = abs(current_rate - prev_rate)
        # Is rate above or below Target?
        vs_target = "أقل من" if current_rate < target_rate else "أعلى من"

        user_prompt = (
            f"بيانات نسبة الوفيات:\n"
            f"- الفصل الحالي: {quarter} {year}، النسبة {current_rate:.2f}%، "
            f"عدد الوفيات {current_deaths} حالة\n"
            f"- الفصل السابق: {prev_quarter}، النسبة {prev_rate:.2f}%، "
            f"عدد الوفيات {prev_deaths} حالة\n"
            f"- الاتجاه: {trend} بمقدار {diff:.2f}%\n"
            f"- الـ Target: {target_rate:.1f}%\n"
            f"- وضع النسبة الحالية: {vs_target} الـ Target\n\n"
            f"اكتب فقرة واحدة تذكر:\n"
            f"1. بلغت نسبة الوفيات {current_rate:.2f}% وعدد الوفيات {current_deaths} حالة\n"
            f"2. مقارنة بالفصل السابق ({prev_rate:.2f}% و {prev_deaths} حالة): {trend} بمقدار {diff:.2f}%\n"
            f"3. النسبة الحالية {vs_target} الـ Target البالغ {target_rate:.1f}%\n"
            f"ممنوع: 'المبلغ عنه' أو نسب نمو مئوية أو أرقام مخترعة."
        )
        return self._safe_generate(user_prompt, max_tokens=170)

    # =========================================================================
    # METHOD 2 — Page 2: Building Distribution
    # FIX-3: always includes bci_rate and rah_rate (patient-rate, not just pct-of-total)
    # =========================================================================

    def analyze_building_distribution(
        self, bci_pct, rah_pct, bci_rate, rah_rate, rah_deaths,
        bci_deaths=0
    ):
        bci_rate_part = (
            f"، معدل الوفيات بين مرضاه {bci_rate:.1f}%" if bci_rate > 0 else ""
        )
        rah_rate_part = (
            f"، معدل الوفيات بين مرضاه {rah_rate:.1f}%" if rah_rate > 0 else ""
        )
        user_prompt = (
            f"توزيع الوفيات بحسب المبنى:\n"
            f"- مركز القلب: {bci_deaths} وفاة ({bci_pct:.0f}% من الإجمالي){bci_rate_part}\n"
            f"- المبنى العام: {rah_deaths} وفاة ({rah_pct:.0f}% من الإجمالي){rah_rate_part}\n\n"
            f"اكتب فقرة تذكر:\n"
            f"1. أي مبنى سجّل عدد وفيات أعلى\n"
            f"2. أي مبنى سجّل نسبة وفيات أعلى بين مرضاه\n"
            f"3. الفرق بين المبنيين في كلا المقياسين\n"
            f"لا تستخدم BCI أو RAH. استخدم 'مركز القلب' و'المبنى العام' فقط."
        )
        return self._safe_generate(user_prompt, max_tokens=160)

    # =========================================================================
    # METHOD 3 — Page 3: Age by Quarter
    # =========================================================================

    def analyze_age_by_quarter(self, current_quarter, prev_quarter, age_changes,
                                under5_note=None):
        under5 = next(
            (g for g in age_changes
             if 'اقل من 5' in g.get('group', '') or 'أقل من 5' in g.get('group', '')),
            None
        )
        others = sorted(
            [g for g in age_changes if g is not under5],
            key=lambda x: abs(x['current'] - x['prev']),
            reverse=True
        )[:2]
        notable = ([under5] if under5 else []) + others
        changes_text = "\n".join([
            f"  - {g['group']}: من {g['prev']} إلى {g['current']} "
            f"({'ارتفاع' if g['current'] > g['prev'] else 'انخفاض'})"
            for g in notable if g
        ])
        children_note = ""
        if under5_note:
            children_note = (
                f"\nملاحظة فئة أقل من 5 سنوات: {under5_note.get('current','')} حالة، "
                f"أعمارهم {under5_note.get('ages_desc','من شهر أو أقل')}، "
                f"تصنيف: {under5_note.get('classification','')}."
            )
        user_prompt = (
            f"مقارنة الوفيات بحسب العمر بين {prev_quarter} و {current_quarter}:\n"
            f"{changes_text}{children_note}\n\n"
            f"اكتب فقرة تبدأ بفئة أقل من 5 سنوات (إن وُجدت تغييرات)، "
            f"ثم الفئات الأخرى ذات التغيير الملحوظ. "
            f"لا تذكر نسب مئوية للنمو، فقط الأعداد."
        )
        return self._safe_generate(user_prompt, max_tokens=170)

    # =========================================================================
    # METHOD 4 — Page 3: Department Analysis
    # FIX-5: each dept listed with exact name+count+% — no AI grouping
    # =========================================================================

    def analyze_departments(
        self, total_deaths, icu_deaths, er_deaths, ward_deaths, top_departments,
        er_details=None, ward_details=None
    ):
        # Each dept listed individually with exact name — prevents AI from grouping
        dept_lines = "\n".join([
            f"  - {d.get('name','')}: {d.get('count',0)} وفاة "
            f"({d.get('percentage',0):.0f}% من إجمالي الوفيات)"
            for d in top_departments
        ])

        er_block = ""
        if er_details and er_details.get('count', 0) > 0:
            specs = "، ".join(er_details.get('specialties', []))
            los_min = er_details.get('los_min', '؟')
            los_max = er_details.get('los_max', '؟')
            er_block = (
                f"\nمرضى الطوارئ المقيمون: {er_details['count']} حالة، "
                f"مدة الإقامة بين {los_min} و{los_max} أيام، "
                f"اختصاصات الأطباء: {specs}."
            )

        ward_block = ""
        if ward_details:
            lines = [
                f"  - {p.get('dept','')} — {p.get('los','')} يوم"
                + (f" — {p['specialty']}" if p.get('specialty') else "")
                for p in ward_details
            ]
            ward_block = (
                f"\nالأقسام الاستشفائية ({ward_deaths} حالة):\n" + "\n".join(lines)
            )

        user_prompt = (
            f"توزيع الوفيات بحسب الأقسام — إجمالي: {total_deaths}\n"
            f"أقسام العناية: {icu_deaths} وفاة | الطوارئ (مقيمون): {er_deaths} | "
            f"الاستشفائية: {ward_deaths}\n\n"
            f"الأقسام بالتفصيل:\n{dept_lines}"
            f"{er_block}{ward_block}\n\n"
            f"اكتب فقرة تذكر كل قسم باسمه الدقيق ونسبته كما هي في البيانات أعلاه. "
            f"لا تجمع الأقسام معاً ولا تغير أسماءها."
        )
        return self._safe_generate(user_prompt, max_tokens=220)

    # =========================================================================
    # METHOD 5 — Page 4: Department Comparison
    # FIX-4: removed growth% from prompt — only absolute numbers shown
    # =========================================================================

    def analyze_dept_comparison(self, current_quarter, prev_quarter, dept_changes):
        top_changes = dept_changes[:5]
        changes_text = "\n".join([
            f"  - {d['name']}: من {d['prev']} إلى {d['current']} "
            f"({'ارتفاع' if d['current'] > d['prev'] else 'انخفاض'}، "
            f"الفرق {abs(d['current'] - d['prev'])} حالة)"
            for d in top_changes
        ])
        user_prompt = (
            f"مقارنة الوفيات بحسب الأقسام بين {prev_quarter} و {current_quarter}:\n"
            f"{changes_text}\n\n"
            f"اكتب فقرة تذكر:\n"
            f"- القسم الذي شهد أكبر ارتفاع بالعدد المطلق\n"
            f"- القسم الذي شهد أكبر انخفاض بالعدد المطلق\n"
            f"لا تذكر نسب مئوية للنمو أو للارتفاع، فقط الأعداد."
        )
        return self._safe_generate(user_prompt, max_tokens=160)

    # =========================================================================
    # METHOD 6 — Page 4: WHO Category  (STATIC in docx_generator — kept for compat)
    # =========================================================================

    def analyze_who_comparison(self, current_quarter, top_categories):
        # NOTE: this is now bypassed — docx_generator._build_who_comparison_text
        # builds the WHO text statically to prevent hallucinated disease names.
        return ""

    # =========================================================================
    # METHOD 7 — Page 5: WHO Diagnosis  (STATIC in docx_generator — kept for compat)
    # =========================================================================

    def analyze_who_diagnosis(self, quarter, year, top_category, top_count):
        # NOTE: this is now bypassed — docx_generator._build_who_diagnosis_text
        # builds the text statically with correct Arabic lookup table.
        return ""


# =============================================================================
# SINGLETON
# =============================================================================
ai_service = AIAnalysisService()