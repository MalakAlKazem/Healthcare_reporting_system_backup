import { useState, useEffect } from 'react';
import axios from 'axios';
import styles from '../styles/Reports.module.css';

const API_URL = 'http://localhost:8000/api/vap';

const GREEN      = 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)';
const GREEN_DARK = '#166534';

/* ── Targets mirror the dashboard ──────────────────────────────────────── */
const TARGETS = { ICU: 25, CCU: 15, CSU: 9.5, ICN: 10, Ped: 5.5, ITU: 25 };
const FLOORS  = Object.keys(TARGETS);

/* ── Build a stats object from a history entry (for the report API) ────── */
function buildStats(entry) {
  const totalVentDays = entry.total_vent_days || 0;
  const totalCases    = entry.total_cases    || 0;
  const overallRate   = totalVentDays > 0
    ? Math.round((totalCases / totalVentDays) * 1000 * 100) / 100
    : 0;

  const floorStats = {};
  FLOORS.forEach(f => {
    const fl = entry.floors?.[f] || {};
    floorStats[f] = {
      cases:           fl.cases           ?? 0,
      ventilator_days: fl.ventilator_days ?? 0,
      rate:            fl.rate            ?? 0,
      target:          fl.target          ?? TARGETS[f],
      pct_of_total:    totalCases > 0
        ? Math.round(((fl.cases ?? 0) / totalCases) * 1000) / 10
        : 0,
    };
  });

  return {
    summary: {
      quarter:         entry.quarter,
      year:            entry.year,
      total_cases:     totalCases,
      total_vent_days: totalVentDays,
      overall_rate:    overallRate,
    },
    floor_stats:      floorStats,
    germs_overall:    entry.germs_overall  || { counts: {}, percentages: {}, total: 0 },
    germs_by_floor:   entry.germs_by_floor || {},
    icu_cases_table:  entry.icu_cases_table || [],
    ccu_cases_table:  entry.ccu_cases_table || [],
    icn_cases_table:  entry.icn_cases_table || [],
    risk_factors:     { counts: {}, percentages: {}, total: 0 },
    diagnoses:        [],
    monthly_trend:    [],
    age_groups:       {},
    genders:          {},
  };
}

/* ═══════════════════════════════════════════════════════════════════════ */
function VapReports({ language }) {
  const [tab,        setTab]        = useState('summary');
  const [generating, setGenerating] = useState(false);
  const [reportUrl,  setReportUrl]  = useState(null);
  const [entry,      setEntry]      = useState(null);
  const [loading,    setLoading]    = useState(true);
  const ar = language === 'ar';

  useEffect(() => {
    axios.get(`${API_URL}/history`)
      .then(res => {
        const entries = Array.isArray(res.data) ? res.data : [];
        setEntry(entries.length > 0 ? entries[entries.length - 1] : null);
      })
      .catch(err => console.error('Failed to load VAP history:', err))
      .finally(() => setLoading(false));
  }, []);

  /* ── Generate report ───────────────────────────────────────────────── */
  const handleGenerateReport = async () => {
    if (!entry) return;
    setGenerating(true);
    setReportUrl(null);
    try {
      const stats = buildStats(entry);
      const response = await axios.post(`${API_URL}/generate-report`, {
        data:    { statistics: stats },
        quarter: entry.quarter,
        year:    entry.year,
      });
      if (response.data.success) {
        const url = `${API_URL}/download-report?fileName=${encodeURIComponent(response.data.fileName)}`;
        setReportUrl(url);
      }
    } catch (err) {
      console.error('VAP report error:', err);
      alert(ar ? 'حدث خطأ في إنشاء التقرير' : 'Error generating report');
    } finally {
      setGenerating(false);
    }
  };

  /* ── Loading ───────────────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className={styles.emptyState} style={{ background: GREEN }}>
        <div className={styles.emptyStateBackground} />
        <div className={styles.emptyStateContent}>
          <div className={styles.emptyStateIconWrapper}>
            <span className={styles.emptyStateIcon}>⏳</span>
          </div>
          <h2 className={styles.emptyStateTitle}>
            {ar ? 'جارٍ التحميل...' : 'Loading...'}
          </h2>
        </div>
      </div>
    );
  }

  /* ── Empty ─────────────────────────────────────────────────────────── */
  if (!entry) {
    return (
      <div className={styles.emptyState} style={{ background: GREEN }}>
        <div className={styles.emptyStateBackground} />
        <div className={styles.emptyStateContent}>
          <div className={styles.emptyStateIconWrapper}>
            <span className={styles.emptyStateIcon}>🫁</span>
          </div>
          <h2 className={styles.emptyStateTitle}>
            {ar ? 'لا توجد بيانات' : 'No VAP Data Available'}
          </h2>
          <p className={styles.emptyStateText}>
            {ar
              ? 'يرجى رفع بيانات VAP أولاً لتتمكن من إنشاء التقرير'
              : 'Please upload VAP data first to generate a report'}
          </p>
        </div>
      </div>
    );
  }

  const totalCases    = entry.total_cases    ?? 0;
  const totalVentDays = entry.total_vent_days ?? 0;
  const overallRate   = totalVentDays > 0
    ? ((totalCases / totalVentDays) * 1000).toFixed(2)
    : '—';

  const statCards = [
    {
      icon: '🦠',
      label:    ar ? 'إجمالي الحالات'      : 'Total Cases',
      value:    totalCases,
      subValue: null,
      progress: Math.min((totalCases / 20) * 100, 100),
      bg:       'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      border:   '#991b1b',
    },
    {
      icon: '🫁',
      label:    ar ? 'إجمالي أيام التنفس' : 'Total Vent Days',
      value:    totalVentDays.toLocaleString(),
      subValue: null,
      progress: 75,
      bg:       'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
      border:   '#1e40af',
    },
    {
      icon: '📊',
      label:    ar ? 'معدل VAP الكلي'     : 'Overall VAP Rate',
      value:    overallRate,
      subValue: '‰',
      progress: 50,
      bg:       GREEN,
      border:   GREEN_DARK,
    },
    {
      icon: '📅',
      label:    ar ? 'الفصل / السنة'      : 'Quarter / Year',
      value:    entry.quarter,
      subValue: entry.year,
      progress: 60,
      bg:       'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      border:   '#5b21b6',
    },
  ];

  /* ── Main render ───────────────────────────────────────────────────── */
  return (
    <div className={styles.reportsContainer}>

      {/* Header */}
      <div className={styles.reportsHeader} style={{ background: GREEN }}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <div className={styles.headerIconWrapper}>
              <span className={styles.headerIcon}>🫁</span>
            </div>
            <div>
              <h1 className={styles.headerTitle}>
                {ar ? 'تقارير VAP' : 'VAP Reports'}
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
            style={{ opacity: generating ? 0.7 : 1, color: GREEN_DARK }}
          >
            <span className={styles.downloadButtonIcon}>📄</span>
            {generating
              ? (ar ? 'جارٍ الإنشاء...' : 'Generating...')
              : (ar ? 'إنشاء تقرير Word' : 'Generate Word Report')}
          </button>
        </div>
      </div>

      {/* Download banner */}
      {reportUrl && (
        <div style={{
          backgroundColor: '#16a34a', color: 'white', padding: '1rem 1.5rem',
          borderRadius: '12px', marginBottom: '1.5rem',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(22,163,74,0.3)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem' }}>✅</span>
            <span style={{ fontWeight: 600 }}>
              {ar ? 'تم إنشاء التقرير بنجاح!' : 'Report Generated Successfully!'}
            </span>
          </div>
          <a
            href={reportUrl}
            download
            style={{
              backgroundColor: 'white', color: '#16a34a',
              padding: '0.5rem 1.5rem', borderRadius: '8px',
              fontWeight: 'bold', textDecoration: 'none',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}
          >
            <span>⬇️</span>
            {ar ? 'تحميل الوثيقة' : 'Download Word Document'}
          </a>
        </div>
      )}

      {/* Tab selector */}
      <div className={styles.typeSelector}>
        <div className={styles.typeSelectorButtons}>
          {[
            { key: 'summary',      icon: '📄', labelAr: 'ملخص الإحصائيات', labelEn: 'Statistics Summary' },
            { key: 'floors',       icon: '🏥', labelAr: 'معدلات الأقسام',   labelEn: 'Floor Rates' },
            { key: 'germs',        icon: '🧫', labelAr: 'توزيع الجراثيم',   labelEn: 'Germ Distribution' },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`${styles.typeButton} ${
                tab === t.key ? styles.typeButtonActive : styles.typeButtonInactive
              }`}
              style={tab === t.key ? { background: GREEN } : {}}
            >
              <span className={styles.typeButtonIcon}>{t.icon}</span>
              {ar ? t.labelAr : t.labelEn}
            </button>
          ))}
        </div>
      </div>

      {/* ── Summary tab ── */}
      {tab === 'summary' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon} style={{ background: GREEN }}>📊</div>
            <h2 className={styles.reportCardTitle} style={{
              background: GREEN,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {ar ? 'ملخص الإحصائيات' : 'Statistics Summary'}
            </h2>
          </div>

          <div className={styles.statsGrid}>
            {statCards.map((card, i) => (
              <div key={i} className={styles.statCard}
                   style={{ background: card.bg, borderLeftColor: card.border }}>
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
                    <div className={styles.statCardProgressBar}
                         style={{ width: `${card.progress}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className={styles.summarySection} style={{
            background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #d1fae5 100%)',
            borderColor: '#16a34a',
          }}>
            <div className={styles.summarySectionHeader}>
              <div className={styles.summarySectionIcon} style={{ background: GREEN }}>
                <span className={styles.summarySectionIconText}>🫁</span>
              </div>
              <h3 className={styles.summarySectionTitle} style={{
                background: GREEN,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>
                {ar ? 'ملخص التقرير' : 'Report Summary'}
              </h3>
            </div>
            <p className={styles.summarySectionText}>
              {ar
                ? `بناءً على بيانات ${entry.quarter} ${entry.year}، تم تسجيل ${totalCases} حالة VAP عبر ${totalVentDays.toLocaleString()} يوم تنفس آلي، بمعدل إجمالي ${overallRate}‰.`
                : `Based on ${entry.quarter} ${entry.year} data, ${totalCases} VAP cases were recorded across ${totalVentDays.toLocaleString()} ventilator days, with an overall rate of ${overallRate}‰.`}
            </p>
          </div>
        </div>
      )}

      {/* ── Floor rates tab ── */}
      {tab === 'floors' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon} style={{ background: GREEN }}>🏥</div>
            <h2 className={styles.reportCardTitle} style={{
              background: GREEN,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {ar ? 'معدلات الأقسام' : 'Floor Rates'}
            </h2>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ background: GREEN, color: 'white' }}>
                  {[
                    ar ? 'القسم'         : 'Department',
                    ar ? 'الحالات'       : 'Cases',
                    ar ? 'أيام التنفس'   : 'Vent Days',
                    ar ? 'المعدل (‰)'    : 'Rate (‰)',
                    ar ? 'الهدف (‰)'     : 'Target (‰)',
                    ar ? 'الحالة'        : 'Status',
                  ].map(h => (
                    <th key={h} style={{ padding: '0.7rem 1rem', textAlign: 'center', fontWeight: 700 }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FLOORS.map((floor, i) => {
                  const fl       = entry.floors?.[floor] || {};
                  const rate     = fl.rate     ?? 0;
                  const target   = fl.target   ?? TARGETS[floor];
                  const isAbove  = rate > target;
                  const hasCases = (fl.cases ?? 0) > 0 || (fl.ventilator_days ?? 0) > 0;
                  return (
                    <tr key={floor} style={{ background: i % 2 === 0 ? '#f0fdf4' : 'white' }}>
                      <td style={{ padding: '0.6rem 1rem', fontWeight: 700, color: '#166534', textAlign: 'center' }}>
                        {floor}
                      </td>
                      <td style={{ padding: '0.6rem 1rem', textAlign: 'center', fontWeight: 600 }}>
                        {fl.cases ?? 0}
                      </td>
                      <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                        {(fl.ventilator_days ?? 0).toLocaleString()}
                      </td>
                      <td style={{
                        padding: '0.6rem 1rem', textAlign: 'center', fontWeight: 700,
                        color: hasCases ? (isAbove ? '#dc2626' : '#16a34a') : '#94a3b8',
                      }}>
                        {hasCases ? `${rate}` : '—'}
                      </td>
                      <td style={{ padding: '0.6rem 1rem', textAlign: 'center', color: '#d97706', fontWeight: 600 }}>
                        {target}
                      </td>
                      <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                        {!hasCases ? (
                          <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>—</span>
                        ) : (
                          <span style={{
                            background: isAbove ? '#fef2f2' : '#f0fdf4',
                            color:      isAbove ? '#dc2626' : '#16a34a',
                            padding: '0.25rem 0.75rem', borderRadius: '999px',
                            fontSize: '0.8rem', fontWeight: 700,
                          }}>
                            {isAbove
                              ? (ar ? '▲ فوق الهدف' : '▲ Above Target')
                              : (ar ? '▼ تحت الهدف' : '▼ Below Target')}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Germ distribution tab ── */}
      {tab === 'germs' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon} style={{ background: GREEN }}>🧫</div>
            <h2 className={styles.reportCardTitle} style={{
              background: GREEN,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {ar ? 'توزيع الجراثيم' : 'Germ Distribution'}
            </h2>
          </div>

          {/* Overall germs */}
          <GermTable
            title={ar ? 'الجراثيم الكلية' : 'Overall Germs'}
            data={entry.germs_overall?.counts || {}}
            green={GREEN} greenDark={GREEN_DARK} ar={ar}
          />

          {/* Per-floor germs */}
          {Object.entries(entry.germs_by_floor || {}).map(([floor, gbd]) => (
            gbd?.counts && Object.keys(gbd.counts).length > 0 ? (
              <GermTable
                key={floor}
                title={ar ? `جراثيم قسم ${floor}` : `${floor} Germs`}
                data={gbd.counts}
                green={GREEN} greenDark={GREEN_DARK} ar={ar}
              />
            ) : null
          ))}
        </div>
      )}

    </div>
  );
}

/* ── Germ table sub-component ─────────────────────────────────────────── */
function GermTable({ title, data, green, greenDark, ar }) {
  const rows = Object.entries(data || {})
    .map(([k, v]) => [k, Number(v)])
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1]);
  const total = rows.reduce((s, [, v]) => s + v, 0);
  if (!rows.length) return null;

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ color: greenDark, fontWeight: 700, marginBottom: '0.75rem' }}>{title}</h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ background: green, color: 'white' }}>
              <th style={{ padding: '0.6rem 1rem', textAlign: ar ? 'right' : 'left' }}>
                {ar ? 'الجرثومة' : 'Germ'}
              </th>
              <th style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                {ar ? 'العدد' : 'Count'}
              </th>
              <th style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                {ar ? 'النسبة' : '%'}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([key, val], i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? '#f0fdf4' : 'white' }}>
                <td style={{ padding: '0.5rem 1rem', color: '#374151' }}>{key}</td>
                <td style={{ padding: '0.5rem 1rem', textAlign: 'center', fontWeight: 600 }}>{val}</td>
                <td style={{ padding: '0.5rem 1rem', textAlign: 'center', color: greenDark }}>
                  {total > 0 ? ((val / total) * 100).toFixed(1) : '0'}%
                </td>
              </tr>
            ))}
            <tr style={{ background: '#dcfce7', fontWeight: 700 }}>
              <td style={{ padding: '0.5rem 1rem', color: greenDark }}>{ar ? 'الإجمالي' : 'Total'}</td>
              <td style={{ padding: '0.5rem 1rem', textAlign: 'center', color: greenDark }}>{total}</td>
              <td style={{ padding: '0.5rem 1rem', textAlign: 'center', color: greenDark }}>100%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default VapReports;
