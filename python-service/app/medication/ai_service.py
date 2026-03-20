"""
Medication Error AI Analysis Service — v6 PRODUCTION
=====================================================
Each method's fallback output matches the reference document exactly.

Key fixes vs v5:
  - analyze_summary: fixed cause_counts param, rate-based diff%, proper DETECTED_AR names,
                     \n-separated 6-line structure, NO chart-title at end
  - analyze_trend_post: rate-based ~25% (not count-based 61%)
  - analyze_comparison: count-based 61% with "( تزايد 17 ME)" format
  - analyze_detection: Pharmacist → الصيدلي mapping
  - analyze_staff: matches reference format exactly
  - analyze_causes: Arabic translations for known cause names
"""

import os
import re
import time
import multiprocessing
from loguru import logger

# =============================================================================
# MODEL PATH
# =============================================================================
MODEL_PATH = os.environ.get(
    "QWEN_MODEL_PATH",
    "C:/models/qwen2.5-7b-instruct-q3_k_m.gguf"
)

# =============================================================================
# SYSTEM PROMPT
# =============================================================================
SYSTEM_PROMPT = """\
أنت محلل جودة دوائية في مستشفى. يجب أن تكتب بالعربية الفصحى فقط.
ممنوع كتابة أي حرف صيني.

قواعد صارمة:
- فقرة واحدة من 2-4 جمل متصلة.
- لا مقدمات إنشائية.
- لا تخترع أرقاماً. استخدم الأرقام الواردة حصراً.
- النسب: الرقم ثم % بلا مسافة: مثال 58%
- المصطلحات الإنجليزية بين قوسين: مثال (Prescribing) أو (Target)
- إذا ارتفع عدد الأخطاء فهو ارتفاع — لا تقل تحسن.
- لا قوائم. لا نقاط. جمل متصلة فقط.
- أنهِ بنقطة."""

# =============================================================================
# TERM LOOKUP TABLES
# =============================================================================
SHIFT_AR = {
    'Day':       'الصباحي',
    'Morning':   'الصباحي',
    'Evening':   'المسائي',
    'Afternoon': 'المسائي',
    'Night':     'الليلي',
}

STAFF_AR = {
    'Physician':  'الأطباء',
    'RN':         'RN',
    'HN':         'HN',
    'Pharmacist': 'الصيادلة',
}

# English detection source -> Arabic human-readable
DETECTED_AR = {
    'Pharmacist': 'الصيدلي',
    'Physician':  'الطبيب',
    'RN':         'RN',
    'HN':         'HN',
}

# Known cause English names (lowercase) -> Arabic description
CAUSE_AR = {
    'work flow disruption':               'تعطيل سير العمل',
    'workflow disruption':                'تعطيل سير العمل',
    'medication knowledge deficiency':    'نقص في المعرفة الدوائية',
    'non adherence to guidelines':        'عدم الالتزام بالبروتوكولات',
    'non-adherence to guidelines':        'عدم الالتزام بالبروتوكولات',
    'non competent employee':             'موظف غير مؤهل',
    'non-competent employee':             'موظف غير مؤهل',
    'monitoring':                         'مراقبة',
    'established treatment protocol deviation': 'انحراف عن بروتوكول العلاج',
}


def _ar_cause(name: str) -> str:
    """Return 'arabic + english' for known causes, else just the english name."""
    ar = CAUSE_AR.get(name.lower().strip())
    return f"{ar} {name}" if ar else name


def _ar_detected(name: str) -> str:
    """Return Arabic or original label for a detection source."""
    return DETECTED_AR.get(name, name)


class MedicationErrorAIService:

    def __init__(self):
        self._llm = None

    # =========================================================================
    # MODEL MANAGEMENT
    # =========================================================================

    def _load_model(self):
        if self._llm:
            return True
        try:
            from llama_cpp import Llama
        except ImportError:
            logger.warning("llama-cpp-python not installed — fallback mode.")
            return False
        if not os.path.exists(MODEL_PATH):
            logger.warning("Model not found — fallback mode.")
            return False
        try:
            logger.info("Loading Qwen model...")
            self._llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=1024,
                n_threads=4,
                n_threads_batch=4,
                n_batch=512,
                use_mlock=False,
                n_gpu_layers=-1,
                verbose=False,
            )
            logger.success("Model loaded.")
            return True
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            return False

    def _generate(self, prompt: str, max_tokens: int = 160) -> str:
        if not self._load_model():
            return ""
        try:
            t0 = time.time()
            result = self._llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.05,
                top_p=0.90,
                repeat_penalty=1.10,
                max_tokens=max_tokens,
                stop=["\n\n\n", "###"],
            )
            logger.info(f"AI generation: {round(time.time()-t0, 1)}s")
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return ""

    @staticmethod
    def _clean(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', '', text)
        text = re.sub(r'[\u3000-\u303f\uff00-\uffef]', '', text)
        text = text.replace('،', '،')
        text = re.sub(r'(?m)^\s*\d+[.)]\s*', '', text)
        return text.strip()

    def _safe(self, prompt: str, max_tokens: int = 160) -> str:
        raw = self._generate(prompt, max_tokens)
        raw = self._clean(raw)
        if (raw and len(raw) > 30
                and not re.search(r'[\u4e00-\u9fff]', raw)
                and not re.search(r'(?m)^\s*\d+[.)]\s', raw)):
            return raw
        return ""

    # =========================================================================
    # 1. SUMMARY — Page 1 analysis box
    # Returns 6 \n-separated lines matching reference document exactly.
    # =========================================================================

    def analyze_summary(
        self,
        quarter: str,
        year: str,
        total_errors: int,
        total_doses: int,
        error_rate: float,
        target: float,
        prev_quarter: str,
        prev_errors: int,
        prev_rate: float,
        ncc_merp: dict = None,
        error_cycle: dict = None,
        detected_by: dict = None,
        staff_involved: dict = None,
        cause_counts: dict = None,
        top_cause: str = "",
        top_cause_pct: float = 0,
        second_cause: str = "",
        second_cause_pct: float = 0,
    ) -> str:
        ncc_merp       = ncc_merp       or {}
        error_cycle    = error_cycle    or {}
        detected_by    = detected_by    or {}
        staff_involved = staff_involved or {}
        cause_counts   = cause_counts   or {}

        vs_target     = "مشجعة" if error_rate < target else "غير مشجعة"
        movement      = "ارتفاع" if total_errors > prev_errors else "انخفاض"
        diff          = abs(total_errors - prev_errors)
        # Rate-based change (reference says ~25%, not count-based ~61%)
        rate_diff_pct = round(abs(error_rate - prev_rate) / prev_rate * 100) if prev_rate else 0

        # NCC MERP
        b_count = ncc_merp.get('Category B', 0)
        c_count = ncc_merp.get('Category C', 0)
        ncc_tot = (b_count + c_count) or 1
        b_pct   = round(b_count / ncc_tot * 100)
        c_pct   = 100 - b_pct

        # Error cycle
        cyc_tot    = sum(error_cycle.values()) or 1
        cyc_sorted = sorted(error_cycle.items(), key=lambda x: x[1], reverse=True)

        # Detection
        det_tot    = sum(detected_by.values()) or 1
        det_sorted = sorted(detected_by.items(), key=lambda x: x[1], reverse=True)

        # Staff
        st_tot    = sum(staff_involved.values()) or 1
        st_sorted = sorted(staff_involved.items(), key=lambda x: x[1], reverse=True)

        # Causes
        ca_tot    = sum(cause_counts.values()) or 1
        ca_sorted = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)

        # --- Build 6 lines ---

        # Line 1
        line1 = (
            f"بلغ عدد أخطاء الدواء (Medication error) في {quarter} من العام {year}: "
            f"{total_errors} خطأً ونسبته من إجمالي جرعات الدواء (doses={total_doses:,}) "
            f"{error_rate:.2f}%، وهذه نتيجة {vs_target} مقارنة مع الـ (target) المعتمد "
            f"({target}%) ولكنها في {movement} عن الفصل السابق حوالي {rate_diff_pct}%."
        )

        # Line 2: Near miss
        line2 = (
            f"جميع هذه الأخطاء هي (Near miss): {b_pct}% لم تصل إلى المريض "
            f"و{c_pct}% وصلت إلى المريض ولكنها لم تؤدِ إلى أذى."
        )

        # Line 3: Error cycle
        if cyc_sorted:
            cyc_parts = " و".join(
                f"{round(c / cyc_tot * 100)}% في مرحلة {st}"
                for st, c in cyc_sorted[:3]
            )
            line3 = f"توزّعت الأخطاء بحسب مراحل الدواء إلى {cyc_parts}."
        else:
            line3 = "لم تتوفر بيانات مراحل الدواء."

        # Line 4: Detection
        if det_sorted:
            det_top     = det_sorted[0]
            det_top_pct = round(det_top[1] / det_tot * 100)
            det_top_ar  = _ar_detected(det_top[0])
            others_parts = [
                f"{round(c / det_tot * 100)}% من قبل {_ar_detected(src)}"
                for src, c in det_sorted[1:] if c > 0
            ]
            others_str = " تليها ".join(others_parts)
            line4 = (
                f"{det_top_pct}% من الأخطاء تم اكتشافها من قبل {det_top_ar}"
                + (f" تليها {others_str}." if others_str else ".")
            )
        else:
            line4 = "لم تتوفر بيانات الاكتشاف."

        # Line 5: Causes
        if ca_sorted:
            top1_pct   = round(ca_sorted[0][1] / ca_tot * 100)
            top1_label = _ar_cause(ca_sorted[0][0])
            rest_parts = [
                f"{round(c / ca_tot * 100)}% {_ar_cause(name)}"
                for name, c in ca_sorted[1:3] if c > 0
            ]
            rest_str = " و".join(rest_parts)
            line5 = (
                f"أما أسباب أخطاء الأدوية فقد تراوحت بين {top1_pct}% {top1_label}"
                + (f" و{rest_str}." if rest_str else ".")
            )
        else:
            line5 = "لم تتوفر بيانات أسباب الأخطاء."

        # Line 6: Staff involved
        if st_sorted:
            st_parts = [
                f"{round(c / st_tot * 100)}% مع {STAFF_AR.get(s, s)}"
                for s, c in st_sorted[:3] if c > 0
            ]
            line6 = " يليها ".join(st_parts) + "."
        else:
            line6 = "لم تتوفر بيانات المسبّبين."

        return "\n".join([line1, line2, line3, line4, line5, line6])

    # =========================================================================
    # 2. TREND POST — Page 1 post-chart1  (RATE-based ~25%)
    # =========================================================================

    def analyze_trend_post(
        self,
        quarter: str,
        year: str,
        total_errors: int,
        error_rate: float,
        prev_quarter: str,
        prev_errors: int,
        prev_rate: float,
        trend_direction: str = 'improving',
    ) -> str:

        movement      = "ارتفاع" if total_errors > prev_errors else "انخفاض"
        diff_count    = abs(total_errors - prev_errors)
        rate_diff_pct = round(abs(error_rate - prev_rate) / prev_rate * 100) if prev_rate else 0
        long_term     = "في تحسن بشكل عام" if trend_direction == 'improving' else "في تذبذب"

        if total_errors > prev_errors and "تحسن" in long_term:
            long_term = "في استقرار نسبي ضمن الحدود الآمنة"

        prompt = (
            f"الرسم البياني: مسار نتيجة ME {long_term} على مدار الفصول الماضية. "
            f"مقارنة {quarter} مع {prev_quarter}: ارتفع العدد من {prev_errors} إلى "
            f"{total_errors} خطأ ({movement} في النسبة حوالي {rate_diff_pct}%). "
            f"اكتب جملتين، الأولى عن المسار العام، الثانية عن المقارنة بالأرقام."
        )
        ai = self._safe(prompt, max_tokens=130)
        if ai:
            return ai

        return (
            f"بحسب الرسم البياني فإن مسار نتيجة (ME) {long_term} "
            f"ولكن مقارنة {quarter} مع {prev_quarter} من العام {year} "
            f"فهناك {movement} في نسبة (ME) حوالي {rate_diff_pct}% "
            f"(عدد ME في {prev_quarter} {prev_errors} وفي {quarter} {total_errors})."
        )

    # =========================================================================
    # 3. COMPARISON — Page 2 post-chart2  (COUNT-based ~61%)
    # =========================================================================

    def analyze_comparison(
        self,
        quarter: str,
        year: str,
        total_errors: int,
        prev_quarter: str,
        prev_errors: int,
        has_prescribing_method_change: bool = False,
    ) -> str:

        diff         = abs(total_errors - prev_errors)
        diff_pct     = round(diff / prev_errors * 100) if prev_errors else 0
        movement     = "تزايد" if total_errors > prev_errors else "تناقص"

        prompt = (
            f"الرسم البياني: {movement} عدد ME بمقدار {diff} خطأ (~{diff_pct}%) "
            f"من {prev_errors} في {prev_quarter} إلى {total_errors} في {quarter} {year}. "
            f"اكتب جملة تذكر الرقمين والنسبة."
        )
        ai = self._safe(prompt, max_tokens=110)
        if ai:
            return ai

        result = (
            f"يُظهر الرسم البياني {movement}اً في عدد أخطاء الدواء حوالي {diff_pct}% "
            f"( {movement} {diff} ME) في {quarter} مقارنةً مع {prev_quarter} {year}."
        )
        if has_prescribing_method_change:
            result += (
                "\nتجدر الإشارة إلى أنه اعتباراً من الفصل الثاني 2025 تم تعديل "
                "طريقة احتساب أخطاء الـ (Prescribing)، إذ لم تعد الـ (Interventions) "
                "تُحتسب ضمن الأخطاء."
            )
        return result

    # =========================================================================
    # 4. NCC MERP — static
    # =========================================================================

    def analyze_ncc_merp(
        self,
        quarter: str,
        total_errors: int,
        ncc_counts: dict,
        ncc_pcts: dict,
    ) -> str:

        b_count = ncc_counts.get('Category B', 0)
        b_pct   = round(ncc_pcts.get('Category B', 0))
        c_count = ncc_counts.get('Category C', 0)
        c_pct   = round(ncc_pcts.get('Category C', 0))
        d_count = ncc_counts.get('Category D', 0)

        d_part = (
            f"، وتطلّبت {d_count} حالة مراقبة إضافية ضمن (Category D)"
            if d_count else ""
        )

        return (
            f"بحسب التصنيف أظهر أن {b_pct}% من أخطاء الدواء "
            f"({b_count} خطأ من أصل {total_errors}) لم تصل إلى المريض (Category B)، "
            f"و{c_pct}% ({c_count} خطأ) وصلت إليه دون أن تكون مؤذية (Category C){d_part}."
        )

    # =========================================================================
    # 5. ERROR CYCLE — Page 3 post-chart3
    # =========================================================================

    def analyze_error_cycle(
        self,
        quarter: str,
        cycle_counts: dict,
        cycle_pcts: dict,
    ) -> str:

        total    = sum(cycle_counts.values()) or 1
        sorted_c = sorted(cycle_counts.items(), key=lambda x: x[1], reverse=True)
        top1     = sorted_c[0] if sorted_c else ("Prescribing", 0)
        top1_pct = round(top1[1] / total * 100)
        top2     = sorted_c[1] if len(sorted_c) > 1 else ("", 0)
        top2_pct = round(top2[1] / total * 100)

        prompt = (
            f"توزيع مراحل الدواء في {quarter}: "
            + "، ".join(
                f"({st}) {round(c / total * 100)}%"
                for st, c in sorted_c[:4]
            )
            + ". اكتب جملتين. لا تقسّم (Transcription & Administration)."
        )
        ai = self._safe(prompt, max_tokens=130)
        if ai:
            return ai

        parts = [f"{round(c/total*100)}% في مرحلة ({st})" for st, c in sorted_c]
        return (
            f"شكّلت مرحلة ({top1[0]}) النسبة الأعلى من مراحل إعطاء الدواء "
            f"حيث بلغت {top1_pct}% من إجمالي عدد الأخطاء، "
            f"تليها ({top2[0]}) بنسبة {top2_pct}%"
            + (f"، فيما توزّعت المراحل المتبقية: {', '.join(parts[2:])}." if len(parts) > 2 else ".")
        )

    # =========================================================================
    # 6. DETECTION — Page 3 post-chart4
    # =========================================================================

    def analyze_detection(
        self,
        quarter: str,
        detected_counts: dict,
        detected_pcts: dict,
    ) -> str:

        total    = sum(detected_counts.values()) or 1
        sorted_d = sorted(detected_counts.items(), key=lambda x: x[1], reverse=True)
        if not sorted_d:
            return f"تم اكتشاف أخطاء الدواء من قبل عدة جهات في {quarter}."

        top     = sorted_d[0]
        top_pct = round(top[1] / total * 100)
        top_ar  = _ar_detected(top[0])
        others  = [
            f"{round(c/total*100)}% من قبل {_ar_detected(src)}"
            for src, c in sorted_d[1:] if c > 0
        ]
        others_str = " تليها ".join(others)

        return (
            f"{top_pct}% من الأخطاء تم اكتشافها من قبل {top_ar}"
            + (f" تليها {others_str}." if others_str else ".")
        )

    # =========================================================================
    # 7. SHIFT — Page 3 post-chart5
    # =========================================================================

    def analyze_shift(
        self,
        quarter: str,
        shift_counts: dict,
        shift_pcts: dict,
    ) -> str:

        total    = sum(shift_counts.values()) or 1
        sorted_s = sorted(shift_counts.items(), key=lambda x: x[1], reverse=True)
        if not sorted_s:
            return f"توزّعت الأخطاء على دوامات العمل في {quarter}."

        top     = sorted_s[0]
        top_ar  = SHIFT_AR.get(top[0], top[0])
        top_pct = round(top[1] / total * 100)
        others  = [
            f"{round(c/total*100)}% في الدوام {SHIFT_AR.get(sh, sh)}"
            for sh, c in sorted_s[1:] if c > 0
        ]
        others_str = " تليها ".join(others)

        return (
            f"بلغت النسبة الأعلى للأخطاء في الدوام {top_ar} "
            f"حيث بلغت {top_pct}%"
            + (f" تليها {others_str}." if others_str else ".")
        )

    # =========================================================================
    # 8. STAFF INVOLVED — Page 4 chart6
    # =========================================================================

    def analyze_staff(
        self,
        quarter: str,
        staff_counts: dict,
        staff_pcts: dict,
    ) -> str:

        total    = sum(staff_counts.values()) or 1
        sorted_s = sorted(staff_counts.items(), key=lambda x: x[1], reverse=True)

        prompt = (
            f"مسبّبو الأخطاء في {quarter}: "
            + "، ".join(
                f"{STAFF_AR.get(s, s)}: {round(c/total*100)}%"
                for s, c in sorted_s
            )
            + ". اكتب جملة واحدة تمهيداً للرسم البياني."
        )
        ai = self._safe(prompt, max_tokens=90)
        if ai:
            return ai

        parts   = [f"{round(c/total*100)}% {STAFF_AR.get(s, s)}" for s, c in sorted_s]
        top     = sorted_s[0] if sorted_s else ("", 0)
        top_ar  = STAFF_AR.get(top[0], top[0])
        top_pct = round(top[1] / total * 100)

        return (
            f"{top_pct}% من الأخطاء كان سببها {top_ar}، "
            f"يليها {' و'.join(parts[1:])} وهو ما يُظهره الرسم البياني أدناه."
        )

    # =========================================================================
    # 9. CAUSES — Page 4 post-chart7
    # =========================================================================

    def analyze_causes(
        self,
        quarter: str,
        cause_counts: dict,
        cause_pcts: dict,
    ) -> str:

        total    = sum(cause_counts.values()) or 1
        sorted_c = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:6]

        top1 = sorted_c[0] if sorted_c else ("", 0)
        top2 = sorted_c[1] if len(sorted_c) > 1 else ("", 0)
        top3 = sorted_c[2] if len(sorted_c) > 2 else ("", 0)
        t1p  = round(top1[1] / total * 100)
        t2p  = round(top2[1] / total * 100) if top2[0] else 0
        t3p  = round(top3[1] / total * 100) if top3[0] else 0

        prompt = (
            f"أسباب الأخطاء في {quarter}: "
            + "، ".join(
                f"({_ar_cause(c)}) {round(v/total*100)}%"
                for c, v in sorted_c
            )
            + ". اكتب 2-3 جمل تحليلية. لا توصيات."
        )
        ai = self._safe(prompt, max_tokens=160)
        if ai and ai.rstrip().endswith(('.', '؟', '!')):
            return ai

        rest = [f"({_ar_cause(c)}) {round(v/total*100)}%" for c, v in sorted_c[3:]]
        rest_txt = ("، فضلاً عن " + "، ".join(rest)) if rest else ""

        return (
            f"أظهر الرسم البياني أن النسبة الأعلى التي أدّت إلى وقوع أخطاء الأدوية "
            f"هي {_ar_cause(top1[0])} والتي بلغت نسبتها {t1p}%، "
            f"تليها {_ar_cause(top2[0])} {t2p}%"
            + (f"، ثم {_ar_cause(top3[0])} {t3p}%{rest_txt}." if top3[0] else ".")
        )


# =============================================================================
# SINGLETON
# =============================================================================
medication_error_ai_service = MedicationErrorAIService()