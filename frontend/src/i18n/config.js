import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  ar: {
    translation: {
      // Navigation
      "dashboard": "لوحة التحكم",
      "upload": "رفع الملفات",
      "analysis": "التحليل",
      "reports": "التقارير",
      
      // Upload Page
      "uploadTitle": "رفع ملف بيانات الوفيات",
      "dragDrop": "اسحب وأفلت ملف Excel هنا",
      "dragDropOrBrowse": "اسحب وأفلت ملف Excel أو تصفح من جهازك",
      "or": "أو",
      "browse": "تصفح الملفات",
      "uploading": "جاري الرفع...",
      "processing": "جاري المعالجة...",
      
      // Dashboard
      "totalDeaths": "إجمالي الوفيات",
      "averageAge": "متوسط العمر",
      "averageLOS": "متوسط مدة الإقامة",
      "maleDeaths": "وفيات الذكور",
      "femaleDeaths": "وفيات الإناث",
      
      // Analysis
      "ageDistribution": "توزيع الأعمار",
      "causesOfDeath": "أسباب الوفاة",
      "monthlyTrend": "الاتجاه الشهري",
      "specialtyAnalysis": "تحليل التخصصات",
      "whoCategories": "تصنيفات منظمة الصحة العالمية",
      
      // Reports
      "generateReport": "إنشاء التقرير",
      "downloadPDF": "تحميل PDF",
      "reportGenerated": "تم إنشاء التقرير بنجاح",
      "aiInsights": "رؤى الذكاء الاصطناعي",
      "recommendations": "التوصيات",
      
      // Common
      "year": "العام",
      "month": "الشهر",
      "age": "العمر",
      "gender": "الجنس",
      "male": "ذكر",
      "female": "أنثى",
      "days": "أيام",
      "loading": "جاري التحميل...",
      "error": "خطأ",
      "success": "نجاح",
      "noDataYet": "لا توجد بيانات بعد",
"uploadDataToGetStarted": "قم برفع ملف البيانات للبدء",
"uploadData": "رفع البيانات",
"overviewOfMortalityData": "نظرة عامة على بيانات الوفيات",
"years": "سنة",
"genderRatio": "نسبة الجنس",
"deaths": "الوفيات",
"genderDistribution": "توزيع الجنس",
"topCausesOfDeath": "أهم أسباب الوفاة",
"dropHere": "أفلت الملف هنا",
"acceptedFormats": "الصيغ المقبولة",
"dataProcessedSuccessfully": "تمت معالجة البيانات بنجاح",
"redirectingToDashboard": "جاري التحويل إلى لوحة التحكم...",
"instructions": "التعليمات",
"instruction1": "تأكد من أن ملف Excel يحتوي على جميع الأعمدة المطلوبة",
"instruction2": "الصيغ المدعومة: .xlsx و .xls",
"instruction3": "سيتم تنظيف البيانات ومعالجتها تلقائياً",
      "noDataForAnalysis": "لا توجد بيانات للتحليل",
      "uploadDataFirst": "يرجى رفع البيانات أولاً",
      "dataAnalysis": "تحليل البيانات",
      "advancedAnalytics": "تحليلات متقدمة",
      "trendAnalysis": "تحليل الاتجاهات",
      "correlationAnalysis": "تحليل الارتباط",
      "avgAge": "متوسط العمر",
      "yearsOld": "سنة",
      "avgLOS": "متوسط مدة الإقامة",
      "elderlyDeaths": "وفيات كبار السن",
      "ageAbove65": "العمر فوق 65",
      "mortalityTrends": "اتجاهات الوفيات",
      "ageVsLOS": "العمر مقابل مدة الإقامة",
      "lengthOfStay": "مدة الإقامة",
      "patients": "المرضى",
      "aiRecommendations": "توصيات الذكاء الاصطناعي",
      "recommendation1": "تحسين بروتوكولات رعاية كبار السن",
      "recommendation2": "مراجعة إجراءات القبول والتشخيص المبكر",
      "recommendation3": "تعزيز برامج الوقاية والتوعية الصحية",
      "noReportsAvailable": "لا توجد تقارير متاحة",
      "uploadDataToGenerateReports": "قم برفع البيانات لإنشاء التقارير",
      "generateAndDownloadReports": "إنشاء وتحميل التقارير",
      "downloadReport": "تحميل تقرير نصي",
      "generateWordReport": "إنشاء تقرير Word",
      "generating": "جاري الإنشاء...",
      "reportGenerated": "تم إنشاء التقرير بنجاح!",
      "downloadWord": "تحميل مستند Word",
      "summaryReport": "التقرير الملخص",
      "detailedReport": "التقرير المفصل",
      "totalDeaths": "إجمالي الوفيات",
      "averageAge": "متوسط العمر",
      "maleDeaths": "وفيات الذكور",
      "femaleDeaths": "وفيات الإناث",
      "reportSummary": "ملخص التقرير",
      "reportDescription": "يحتوي هذا التقرير على {{total}} حالة وفاة بمتوسط عمر {{avgAge}} سنة",
      "recordNumber": "رقم السجل",
      "showingFirst50Records": "عرض أول 50 سجل من إجمالي {{total}}"
    }
  },
  en: {
    translation: {
      // Navigation
      "dashboard": "Dashboard",
      "upload": "Upload",
      "analysis": "Analysis",
      "reports": "Reports",
      
      // Upload Page
      "uploadTitle": "Upload Mortality Data File",
      "dragDrop": "Drag & drop Excel file here",
      "dragDropOrBrowse": "Drag & drop Excel file or browse from your device",
      "or": "or",
      "browse": "Browse Files",
      "uploading": "Uploading...",
      "processing": "Processing...",
      
      // Dashboard
      "totalDeaths": "Total Deaths",
      "averageAge": "Average Age",
      "averageLOS": "Average Length of Stay",
      "maleDeaths": "Male Deaths",
      "femaleDeaths": "Female Deaths",
      
      // Analysis
      "ageDistribution": "Age Distribution",
      "causesOfDeath": "Causes of Death",
      "monthlyTrend": "Monthly Trend",
      "specialtyAnalysis": "Specialty Analysis",
      "whoCategories": "WHO Categories",
      
      // Reports
      "generateReport": "Generate Report",
      "downloadPDF": "Download PDF",
      "reportGenerated": "Report Generated Successfully",
      "aiInsights": "AI Insights",
      "recommendations": "Recommendations",
      
      // Common
      "year": "Year",
      "month": "Month",
      "age": "Age",
      "gender": "Gender",
      "male": "Male",
      "female": "Female",
      "days": "days",
      "loading": "Loading...",
      "error": "Error",
      "success": "Success",
      "noDataYet": "No Data Yet",
"uploadDataToGetStarted": "Upload data file to get started",
"uploadData": "Upload Data",
"overviewOfMortalityData": "Overview of Mortality Data",
"years": "years",
"genderRatio": "Gender Ratio",
"deaths": "Deaths",
"genderDistribution": "Gender Distribution",
"topCausesOfDeath": "Top Causes of Death",
"dropHere": "Drop file here",
"acceptedFormats": "Accepted formats",
"dataProcessedSuccessfully": "Data processed successfully",
"redirectingToDashboard": "Redirecting to dashboard...",
"instructions": "Instructions",
"instruction1": "Ensure Excel file contains all required columns",
"instruction2": "Supported formats: .xlsx and .xls",
"instruction3": "Data will be automatically cleaned and processed",
      "noDataForAnalysis": "No Data for Analysis",
      "uploadDataFirst": "Please upload data first",
      "dataAnalysis": "Data Analysis",
      "advancedAnalytics": "Advanced Analytics",
      "trendAnalysis": "Trend Analysis",
      "correlationAnalysis": "Correlation Analysis",
      "avgAge": "Average Age",
      "yearsOld": "years old",
      "avgLOS": "Average Length of Stay",
      "elderlyDeaths": "Elderly Deaths",
      "ageAbove65": "Age above 65",
      "mortalityTrends": "Mortality Trends",
      "ageVsLOS": "Age vs Length of Stay",
      "lengthOfStay": "Length of Stay",
      "patients": "Patients",
      "aiRecommendations": "AI Recommendations",
      "recommendation1": "Improve elderly care protocols",
      "recommendation2": "Review admission procedures and early diagnosis",
      "recommendation3": "Enhance prevention and health awareness programs",
      "noReportsAvailable": "No Reports Available",
      "uploadDataToGenerateReports": "Upload data to generate reports",
      "generateAndDownloadReports": "Generate and Download Reports",
      "downloadReport": "Download Text Report",
      "generateWordReport": "Generate Word Report",
      "generating": "Generating...",
      "reportGenerated": "Report Generated Successfully!",
      "downloadWord": "Download Word Document",
      "summaryReport": "Summary Report",
      "detailedReport": "Detailed Report",
      "totalDeaths": "Total Deaths",
      "averageAge": "Average Age",
      "maleDeaths": "Male Deaths",
      "femaleDeaths": "Female Deaths",
      "reportSummary": "Report Summary",
      "reportDescription": "This report contains {{total}} death cases with an average age of {{avgAge}} years",
      "recordNumber": "Record Number",
      "showingFirst50Records": "Showing first 50 records out of {{total}}"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'ar', // Default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;