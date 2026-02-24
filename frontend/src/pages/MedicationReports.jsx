import { useState } from 'react';
import axios from 'axios';
import styles from '../styles/Reports.module.css';

const API_URL = 'http://localhost:8000/api/medication';

const TEAL = 'linear-gradient(135deg, #0d9488 0%, #0891b2 100%)';
const TEAL_DARK = '#0f766e';

function MedicationReports({ data, language }) {
  const [reportType, setReportType] = useState('summary');
  const [generating, setGenerating] = useState(false);
  const [reportUrl, setReportUrl] = useState(null);
  const ar = language === 'ar';

  const handleGenerateReport = async () => {
    if (!data) return;
    setGenerating(true);
    try {
      const response = await axios.post(`${API_URL}/generate-report`, {
        data: { statistics: data.statistics },
        quarter: data.quarter,
        year: data.year,
      });
      if (response.data.success) {
        const url = `${API_URL}/download-report?fileName=${encodeURIComponent(response.data.fileName)}`;
        setReportUrl(url);
      }
    } catch (err) {
      console.error('Report generation error:', err);
      alert(ar ? 'حدث خطأ في إنشاء التقرير' : 'Error generating report');
    } finally {
      setGenerating(false);
    }
  };

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!data) {
    return (
      <div className={styles.emptyState} style={{ background: TEAL }}>
        <div className={styles.emptyStateBackground} />
        <div className={styles.emptyStateContent}>
          <div className={styles.emptyStateIconWrapper}>
            <span className={styles.emptyStateIcon}>💊</span>
          </div>
          <h2 className={styles.emptyStateTitle}>
            {ar ? 'لا توجد بيانات' : 'No Data Available'}
          </h2>
          <p className={styles.emptyStateText}>
            {ar
              ? 'يرجى رفع بيانات أخطاء الدواء أولاً لتتمكن من إنشاء التقرير'
              : 'Please upload medication error data first to generate a report'}
          </p>
        </div>
      </div>
    );
  }

  const sm = data.statistics?.summary || {};
  const totalErrors = sm.total_errors ?? 0;
  const totalDoses  = (sm.total_doses ?? 0).toLocaleString();
  const errorRate   = sm.error_rate != null ? Number(sm.error_rate).toFixed(4) : '—';

  const statCards = [
    {
      icon: '⚠️',
      label: ar ? 'إجمالي الأخطاء' : 'Total Errors',
      value: totalErrors,
      subValue: null,
      progress: 100,
      bg: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      border: '#991b1b',
    },
    {
      icon: '💉',
      label: ar ? 'إجمالي الجرعات' : 'Total Doses',
      value: totalDoses,
      subValue: null,
      progress: 75,
      bg: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
      border: '#1e40af',
    },
    {
      icon: '📉',
      label: ar ? 'معدل الخطأ' : 'Error Rate',
      value: errorRate,
      subValue: '%',
      progress: 50,
      bg: TEAL,
      border: TEAL_DARK,
    },
    {
      icon: '📅',
      label: ar ? 'الفصل / السنة' : 'Quarter / Year',
      value: data.quarter,
      subValue: data.year,
      progress: 60,
      bg: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      border: '#5b21b6',
    },
  ];

  const records = data.records || [];

  // ── Main view ────────────────────────────────────────────────────────────
  return (
    <div className={styles.reportsContainer}>

      {/* Header */}
      <div className={styles.reportsHeader} style={{ background: TEAL }}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <div className={styles.headerIconWrapper}>
              <span className={styles.headerIcon}>💊</span>
            </div>
            <div>
              <h1 className={styles.headerTitle}>
                {ar ? 'تقارير أخطاء الدواء' : 'Medication Error Reports'}
              </h1>
              <p className={styles.headerSubtitle}>
                {ar
                  ? 'توليد وتحميل تقرير Word التفصيلي'
                  : 'Generate and download the detailed Word report'}
              </p>
            </div>
          </div>
          <button
            onClick={handleGenerateReport}
            className={styles.downloadButton}
            disabled={generating}
            style={{ opacity: generating ? 0.7 : 1, color: TEAL_DARK }}
          >
            <span className={styles.downloadButtonIcon}>📄</span>
            {generating
              ? (ar ? 'جارٍ الإنشاء...' : 'Generating...')
              : (ar ? 'إنشاء تقرير Word' : 'Generate Word Report')}
          </button>
        </div>
      </div>

      {/* Download link banner */}
      {reportUrl && (
        <div style={{
          backgroundColor: '#0d9488',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(13,148,136,0.3)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem' }}>✅</span>
            <span style={{ fontWeight: 600 }}>
              {ar ? 'تم إنشاء التقرير بنجاح!' : 'Word Report Generated Successfully!'}
            </span>
          </div>
          <a
            href={reportUrl}
            download
            style={{
              backgroundColor: 'white',
              color: '#0d9488',
              padding: '0.5rem 1.5rem',
              borderRadius: '8px',
              fontWeight: 'bold',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span>⬇️</span>
            {ar ? 'تحميل الوثيقة' : 'Download Word Document'}
          </a>
        </div>
      )}

      {/* Report type selector */}
      <div className={styles.typeSelector}>
        <div className={styles.typeSelectorButtons}>
          <button
            onClick={() => setReportType('summary')}
            className={`${styles.typeButton} ${styles.typeButtonSummary} ${
              reportType === 'summary' ? styles.typeButtonActive : styles.typeButtonInactive
            }`}
            style={reportType === 'summary' ? { background: TEAL } : {}}
          >
            <span className={styles.typeButtonIcon}>📄</span>
            {ar ? 'ملخص الإحصائيات' : 'Summary Report'}
          </button>
          <button
            onClick={() => setReportType('detailed')}
            className={`${styles.typeButton} ${styles.typeButtonDetailed} ${
              reportType === 'detailed' ? styles.typeButtonActive : styles.typeButtonInactive
            }`}
            style={reportType === 'detailed' ? { background: TEAL } : {}}
          >
            <span className={styles.typeButtonIcon}>📋</span>
            {ar ? 'البيانات التفصيلية' : 'Detailed Records'}
          </button>
        </div>
      </div>

      {/* ── Summary view ── */}
      {reportType === 'summary' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon} style={{ background: TEAL }}>📊</div>
            <h2 className={styles.reportCardTitle} style={{
              background: TEAL,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {ar ? 'ملخص الإحصائيات' : 'Statistics Summary'}
            </h2>
          </div>

          <div className={styles.statsGrid}>
            {statCards.map((card, i) => (
              <div
                key={i}
                className={styles.statCard}
                style={{ background: card.bg, borderLeftColor: card.border }}
              >
                <div className={styles.statCardContent}>
                  <div className={styles.statCardHeader}>
                    <div className={styles.statCardIconWrapper}>
                      <span className={styles.statCardIcon}>{card.icon}</span>
                    </div>
                    <h3 className={styles.statCardLabel}>{card.label}</h3>
                  </div>
                  <div className={styles.statCardValue}>
                    {card.value}
                    {card.subValue && (
                      <span className={styles.statCardSubValue}>{card.subValue}</span>
                    )}
                  </div>
                  <div className={styles.statCardProgress}>
                    <div
                      className={styles.statCardProgressBar}
                      style={{ width: `${card.progress}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className={styles.summarySection} style={{
            background: 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 50%, #cffafe 100%)',
            borderColor: '#0d9488',
          }}>
            <div className={styles.summarySectionHeader}>
              <div className={styles.summarySectionIcon} style={{ background: TEAL }}>
                <span className={styles.summarySectionIconText}>💊</span>
              </div>
              <h3 className={styles.summarySectionTitle} style={{
                background: TEAL,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>
                {ar ? 'ملخص التقرير' : 'Report Summary'}
              </h3>
            </div>
            <p className={styles.summarySectionText}>
              {ar
                ? `بناءً على بيانات ${data.quarter} ${data.year}، تم تسجيل ${totalErrors} خطأ دوائي من أصل ${totalDoses} جرعة موزعة، بمعدل خطأ ${errorRate}%.`
                : `Based on ${data.quarter} ${data.year} data, ${totalErrors} medication errors were recorded out of ${totalDoses} doses dispensed, with an error rate of ${errorRate}%.`}
            </p>
          </div>
        </div>
      )}

      {/* ── Detailed records view ── */}
      {reportType === 'detailed' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon} style={{ background: TEAL }}>📋</div>
            <h2 className={styles.reportCardTitle} style={{
              background: TEAL,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {ar ? 'البيانات التفصيلية' : 'Detailed Records'}
            </h2>
          </div>

          <div className={styles.tableWrapper}>
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead className={styles.tableHead} style={{ background: TEAL }}>
                  <tr className={styles.tableHeadRow}>
                    {[
                      { icon: '🔢', label: ar ? 'رقم' : '#' },
                      { icon: '⚠️', label: ar ? 'نوع الخطأ' : 'Error Type' },
                      { icon: '🔄', label: ar ? 'مرحلة الدورة' : 'Error Stage' },
                      { icon: '👁️', label: ar ? 'الكاشف' : 'Detected By' },
                      { icon: '🕐', label: ar ? 'الوردية' : 'Shift' },
                    ].map((col, i) => (
                      <th key={i} className={styles.tableHeadCell}>
                        <div className={styles.tableHeadCellContent}>
                          <span className={styles.tableHeadCellIcon}>{col.icon}</span>
                          {col.label}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className={styles.tableBody}>
                  {records.slice(0, 50).map((record, index) => (
                    <tr key={index} className={styles.tableBodyRow}>
                      <td className={styles.tableBodyCell}>
                        <div className={styles.tableCellNumber}>
                          <div
                            className={styles.tableCellNumberBadge}
                            style={{ background: TEAL }}
                          >
                            {index + 1}
                          </div>
                        </div>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={styles.tableCellAge}>
                          {record.error_type || record['Error type'] || '—'}
                        </span>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={styles.tableCellMonthBadge} style={{
                          background: 'linear-gradient(135deg, #f0fdfa, #ccfbf1)',
                          color: TEAL_DARK,
                          borderColor: '#0d9488',
                        }}>
                          {record.error_cycle || record['Stage of medication process'] || '—'}
                        </span>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={styles.tableCellLOS}>
                          {record.detected_by || record['Detected by'] || '—'}
                        </span>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span
                          className={styles.tableCellGenderBadge}
                          style={{ background: TEAL }}
                        >
                          {record.duty_shift || record['Duty shift'] || '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {records.length > 50 && (
            <div className={styles.tableInfoBanner}>
              <p className={styles.tableInfoText}>
                <span className={styles.tableInfoIcon}>ℹ️</span>
                {ar
                  ? `عرض أول 50 سجل من أصل ${records.length}`
                  : `Showing first 50 records out of ${records.length}`}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MedicationReports;
