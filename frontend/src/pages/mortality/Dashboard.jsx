import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/Dashboard.module.css';
import { AreaChart, Area } from 'recharts';
import { HistoricalComparisonsSection } from './HistoricalComparisons';
import { LabelList } from 'recharts';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart,
} from 'recharts';

// ─── Palette ──────────────────────────────────────────────────────────────────
const COLORS = [
  '#2563ea', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#06b6d4', '#f97316', '#84cc16',
  '#ec4899', '#14b8a6', '#a855f7', '#fb923c', '#22d3ee',
];
const BUILDING_COLORS = {   rah: '#2563ea',
  bci: '#16a34a'
 };
const CMP_CURRENT  = '#3b82f6';
const CMP_PREV     = '#10b981';
const CMP_LASTYEAR = '#f59e0b';

// ─── Shared tooltip style ─────────────────────────────────────────────────────
const TS = {
  contentStyle: {
    background: '#fff', border: '1px solid #e2e8f0', borderRadius: '10px',
    padding: '10px 14px', boxShadow: '0 4px 16px rgba(0,0,0,0.08)', fontSize: '12px',
  },
};

// ─── Quarter sort key ─────────────────────────────────────────────────────────
const QUARTER_ORDER = {
  'الفصل الأول': 1, 'الفصل الاول': 1,
  'الفصل الثاني': 2, 'الفصل الثالث': 3, 'الفصل الرابع': 4,
};
function quarterSortKey(h) {
  return (parseInt(h.year) || 0) * 10 + (QUARTER_ORDER[h.quarter] || 0);
}

// ─── KPI Change Badge ─────────────────────────────────────────────────────────
function ChangeBadge({ label, current, previous, lowerIsBetter = true }) {
  if (previous == null || previous === 0 || current == null) return null;
  const delta = ((current - previous) / Math.abs(previous)) * 100;
  const isImprovement = lowerIsBetter ? delta < 0 : delta > 0;
  const arrow = delta > 0 ? '▲' : '▼';
  const color = isImprovement ? '#16a34a' : '#dc2626';
  const bg    = isImprovement ? '#f0fdf4' : '#fef2f2';
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 10, fontWeight: 600, color, background: bg, borderRadius: 8, padding: '2px 7px', marginTop: 2 }}>
      {arrow} {Math.abs(delta).toFixed(1)}%
      <span style={{ color: '#94a3b8', fontWeight: 400 }}>{label}</span>
    </div>
  );
}

// ─── Trend Chart ──────────────────────────────────────────────────────────────
function TrendChart({ historyData }) {
  return (
    <div className={styles.chartCard} style={{ marginBottom: '1.5rem' }}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Inpatient Mortality Rate vs Target (T &lt; 1.65%)</h3>
      </div>
      <div className={styles.chartBody}>
        <ResponsiveContainer width="100%" height={430}>
          <LineChart data={historyData.map(h => ({ label: `${h.quarter} ${h.year}`, rate: h.rate, target: 1.65 }))}
            margin={{ top: 16, right: 20, left: 0, bottom: 70 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="label" stroke="#94a3b8" tick={{ fontSize: 9, fill: '#64748b' }} interval={0} angle={-45} textAnchor="end" height={75} />
            <YAxis domain={[0, Math.max(...historyData.map(h => h.rate), 2) + 0.5]} stroke="#94a3b8" tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
            <Tooltip {...TS} formatter={(v, name) => [`${v}%`, name]} />
            <Legend verticalAlign="top" height={32} />
            <Line type="monotone" dataKey="rate" name="Result" stroke="#3b82f6" strokeWidth={3}
              dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 6 }}
              label={{ position: 'top', fontSize: 9, fill: '#3b82f6', formatter: v => `${v}%` }} />
            <Line type="monotone" dataKey="target" name="Target (1.65%)" stroke="#58707c" strokeWidth={2} strokeDasharray="6 3" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── Age Group Comparison Chart ───────────────────────────────────────────────
const AGE_SHORT = ['<5', '5-15', '16-30', '31-50', '51-60', '61-70', '71-80', '81+'];

function AgeComparisonChart({ currentLabel, prevLabel, lastYearLabel, currentAges, prevAges, lastYearAges }) {
  const data = AGE_SHORT.map((name, i) => {
    const row = { name, [currentLabel]: currentAges[i] ?? 0 };
    if (prevAges)     row[prevLabel]     = prevAges[i]     ?? 0;
    if (lastYearAges) row[lastYearLabel] = lastYearAges[i] ?? 0;
    return row;
  });

  return (
    <div className={styles.chartCard} style={{ marginBottom: '1.5rem' }}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Age Group Comparison — تصنيف العمر</h3>
      </div>
      <div className={styles.chartBody}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 10, fill: '#64748b' }} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip {...TS} />
            <Legend verticalAlign="top" height={32} />
            <Bar dataKey={currentLabel}  fill={CMP_CURRENT}  radius={[4,4,0,0]} maxBarSize={18} />
            {prevAges     && <Bar dataKey={prevLabel}     fill={CMP_PREV}     radius={[4,4,0,0]} maxBarSize={18} />}
            {lastYearAges && <Bar dataKey={lastYearLabel} fill={CMP_LASTYEAR} radius={[4,4,0,0]} maxBarSize={18} />}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── Department Comparison Chart ──────────────────────────────────────────────
function DeptComparisonChart({ currentLabel, prevLabel, lastYearLabel, currentDepts, prevDepts, lastYearDepts }) {
  const allDepts = Array.from(new Set([
    ...Object.keys(currentDepts  || {}),
    ...Object.keys(prevDepts     || {}),
    ...Object.keys(lastYearDepts || {}),
  ]));

  const data = allDepts.map(dept => {
    const row = { dept, [currentLabel]: currentDepts?.[dept] ?? 0 };
    if (prevDepts)     row[prevLabel]     = prevDepts?.[dept]     ?? 0;
    if (lastYearDepts) row[lastYearLabel] = lastYearDepts?.[dept] ?? 0;
    return row;
  }).sort((a, b) => b[currentLabel] - a[currentLabel]);

  return (
    <div className={styles.chartCard} style={{ marginBottom: '1.5rem' }}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Department Comparison — القسم التمريضي</h3>
      </div>
      <div className={styles.chartBody}>
        <ResponsiveContainer width="100%" height={Math.max(300, data.length * 42)}>
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
            <XAxis type="number" stroke="#94a3b8" tick={{ fontSize: 11 }} allowDecimals={false} />
            <YAxis type="category" dataKey="dept" stroke="#94a3b8" tick={{ fontSize: 11 }} width={58} />
            <Tooltip {...TS} />
            <Legend verticalAlign="top" height={32} />
            <Bar dataKey={currentLabel}  fill={CMP_CURRENT}  radius={[0,4,4,0]} maxBarSize={12} />
            {prevDepts     && <Bar dataKey={prevLabel}     fill={CMP_PREV}     radius={[0,4,4,0]} maxBarSize={12} />}
            {lastYearDepts && <Bar dataKey={lastYearLabel} fill={CMP_LASTYEAR} radius={[0,4,4,0]} maxBarSize={12} />}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── Pie label ────────────────────────────────────────────────────────────────
const PieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null;
  const R = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.58;
  return (
    <text x={cx + r * Math.cos(-midAngle * R)} y={cy + r * Math.sin(-midAngle * R)}
      fill="#fff" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={700}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

// ─── Semicircle Gauge ─────────────────────────────────────────────────────────
function MortalityGauge({ rate, target }) {
  const MAX = 10;
  const ratePct = Math.min(rate, MAX) / MAX;
  const tgtPct  = Math.min(target, MAX) / MAX;
  const isAbove = rate > target;
  const arc = (pct, radius) => {
    const angle = Math.PI * pct;
    const x = 100 - radius * Math.cos(angle);
    const y = 100 - radius * Math.sin(angle);
    return `M ${100 - radius} 100 A ${radius} ${radius} 0 ${pct > 0.5 ? 1 : 0} 1 ${x} ${y}`;
  };
  return (
    <div style={{ textAlign: 'center' }}>
      <svg viewBox="0 0 200 110" width="300">
        <path d={arc(1, 70)} fill="none" stroke="#e2e8f0" strokeWidth="18" strokeLinecap="round" />
        <path d={arc(ratePct, 70)} fill="none" stroke={isAbove ? '#ef4444' : '#10b981'} strokeWidth="14" strokeLinecap="round" />
        <line x1={100 - 62 * Math.cos(Math.PI * tgtPct)} y1={100 - 62 * Math.sin(Math.PI * tgtPct)}
          x2={100 - 80 * Math.cos(Math.PI * tgtPct)} y2={100 - 80 * Math.sin(Math.PI * tgtPct)}
          stroke="#f59e0b" strokeWidth="3.5" strokeLinecap="round" />
        <text x="100" y="86" textAnchor="middle" fontSize="26" fontWeight="800" fill={isAbove ? '#ef4444' : '#10b981'}>
          {rate.toFixed(2)}%
        </text>
        <text x="100" y="102" textAnchor="middle" fontSize="10" fill="#94a3b8">target {target}%</text>
      </svg>
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: isAbove ? '#fef2f2' : '#f0fdf4', color: isAbove ? '#dc2626' : '#16a34a', borderRadius: 20, padding: '5px 16px', fontSize: 12, fontWeight: 700, marginTop: 4 }}>
        {isAbove ? '▲ Above Target' : '▼ Below Target'}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 14, fontSize: 12, color: '#64748b' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#1e293b' }}>{rate.toFixed(2)}%</div>
          <div>Actual Rate</div>
        </div>
        <div style={{ width: 1, background: '#e2e8f0' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#f59e0b' }}>{target}%</div>
          <div>Target</div>
        </div>
        <div style={{ width: 1, background: '#e2e8f0' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: isAbove ? '#ef4444' : '#10b981' }}>
            {Math.abs(rate - target).toFixed(2)}%
          </div>
          <div>{isAbove ? 'Over' : 'Under'}</div>
        </div>
      </div>
    </div>
  );
}

// ─── Table styles ─────────────────────────────────────────────────────────────
const TH = { padding: '10px 12px', textAlign: 'left', fontWeight: 700, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em', borderBottom: '1px solid #e2e8f0', whiteSpace: 'nowrap' };
const TD = { padding: '9px 12px', color: '#475569', verticalAlign: 'middle' };

// ═════════════════════════════════════════════════════════════════════════════
// Dashboard
// ═════════════════════════════════════════════════════════════════════════════
function Dashboard({ data, totalPatients = 0, quarter = '', year = '', historyData = [] }) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const MORTALITY_TARGET = 1.65;

  // ─── Comparison quarters ───────────────────────────────────────────────────
  const currentKey = quarterSortKey({ quarter, year });

  const prevQuarter = historyData.length > 0
    ? [...historyData].filter(h => quarterSortKey(h) < currentKey).sort((a,b) => quarterSortKey(b) - quarterSortKey(a))[0] ?? null
    : null;
  const qMap = { 'الفصل الاول': 'Q1', 'الفصل الأول': 'Q1', 'الفصل الثاني': 'Q2', 'الفصل الثالث': 'Q3', 'الفصل الرابع': 'Q4' };
  const currentQShort = `${qMap[quarter] || quarter} ${year}`;
  const allThisYear = historyData
    .filter(h => h.year === year && !(h.quarter === quarter))
    .sort((a, b) => quarterSortKey(a) - quarterSortKey(b));

  const lastYearQuarter = historyData.find(
    h => h.quarter === quarter && h.year === String(parseInt(year) - 1)
  ) ?? null;

  const labelCurrent  = quarter ? `${quarter} ${year}` : 'Current';
  const labelPrev     = prevQuarter     ? `${prevQuarter.quarter} ${prevQuarter.year}`         : null;
  const labelLastYear = lastYearQuarter ? `${lastYearQuarter.quarter} ${lastYearQuarter.year}` : null;

  useEffect(() => { if (data) calculateStatistics(data); }, [data]);

  const calculateStatistics = (mortalityData) => {
    if (!mortalityData?.records || !Array.isArray(mortalityData.records)) return;
    const records = mortalityData.records.filter(r => r.include_kpi?.toString().toLowerCase().trim() === 'yes');
    if (!records.length) return;

    const totalDeaths    = records.length;
    const averageAge     = records.reduce((s,r) => s + (parseFloat(r.age)||0), 0) / totalDeaths;
    const averageLOS     = records.reduce((s,r) => s + (parseFloat(r.length_of_stay)||0), 0) / totalDeaths;
    const maleDeaths     = records.filter(r => r.gender === 'ذكر'  || r.gender?.toLowerCase() === 'male').length;
    const femaleDeaths   = records.filter(r => r.gender === 'انثى' || r.gender?.toLowerCase() === 'female').length;
    const malePercentage = ((maleDeaths / totalDeaths) * 100).toFixed(1);
    const mortalityRate  = totalPatients > 0 ? (totalDeaths / totalPatients) * 100 : null;

    const monthlyData = {};
    records.forEach(r => { const m = r.month||'Unknown'; monthlyData[m]=(monthlyData[m]||0)+1; });
    const monthlyChart = Object.entries(monthlyData)
      .map(([month,count]) => ({ month: getMonthName(month, i18n.language), deaths: count, _key: parseInt(month) }))
      .sort((a,b) => a._key - b._key);

    const causesCount = {};
    records.forEach(r => { const c = r.direct_cause_of_death||'Unknown'; causesCount[c]=(causesCount[c]||0)+1; });
    const topCauses = Object.entries(causesCount).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([cause,count])=>({cause,count}));

    const bldgCount = {};
    records.forEach(r => { const b=(r.building||'Unknown').trim().toLowerCase(); bldgCount[b]=(bldgCount[b]||0)+1; });
    const buildingChart = Object.entries(bldgCount).sort((a,b)=>b[1]-a[1]).map(([name,value])=>({name,value}));

    const entryCount = {};
    records.forEach(r => { const e=r.admission_source_category||'Unknown'; entryCount[e]=(entryCount[e]||0)+1; });
    const entryChart = Object.entries(entryCount).sort((a,b)=>b[1]-a[1]).map(([name,count])=>({name,count}));

    const AGE_ORDER = ['اقل من 5 سنوات','من 5 الى 15 سنة','من 16 الى 30 سنة','من 31 الى 50 سنة','من 51 الى 60 سنة','من 61 الى 70 سنة','من 71 الى 80 سنة','اكثر من 81 سنة'];
    const ageCount = {};
    records.forEach(r => { const a=r.age_group||'Unknown'; ageCount[a]=(ageCount[a]||0)+1; });
    const ageChart = AGE_ORDER.filter(k=>ageCount[k]).map((name,i)=>({name, count:ageCount[name], color:COLORS[i%COLORS.length]}));
    const ageArray = AGE_ORDER.map(k => ageCount[k] || 0);

    const deptCount = {};
    records.forEach(r => { const d=r.nursing_department||'Unknown'; deptCount[d]=(deptCount[d]||0)+1; });
    const deptChart = Object.entries(deptCount).sort((a,b)=>b[1]-a[1]).map(([dept,count],i)=>({dept,count,color:COLORS[i%COLORS.length]}));

    const whoCount = {};
    records.forEach(r => { const w=r.who_category_1||'Unknown'; whoCount[w]=(whoCount[w]||0)+1; });
    let cum = 0;
    const whoChart = Object.entries(whoCount).sort((a,b)=>b[1]-a[1]).map(([cat,count],i)=>{
      cum += count;
      return { cat, count, cumPct: parseFloat(((cum/totalDeaths)*100).toFixed(1)), color:COLORS[i%COLORS.length] };
    });

    setStats({ totalDeaths, averageAge: averageAge.toFixed(1), averageLOS: averageLOS.toFixed(1),
      maleDeaths, femaleDeaths, malePercentage, mortalityRate,
      monthlyChart, topCauses, buildingChart, entryChart, ageChart, ageArray, deptChart, deptCount, whoChart });
  };

  const getMonthName = (monthNum, lang) => {
    const ar = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
    const en = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const idx = parseInt(monthNum) - 1;
    return lang === 'ar' ? ar[idx]||monthNum : en[idx]||monthNum;
  };

  if (!data) return (
    <div className={styles.dashboard} dir="ltr">
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📊</div>
        <h2 className={styles.emptyTitle}>{t('noDataYet')}</h2>
        <p className={styles.emptyText}>{t('uploadDataToGetStarted')}</p>
        <button onClick={() => navigate('/upload')} className={styles.uploadButton}>
          <span>📤</span><span>{t('uploadData')}</span>
        </button>
      </div>
    </div>
  );

  if (!stats) return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>⏳</div>
      <h2 className={styles.emptyTitle}>{t('processing')}</h2>
      <p className={styles.emptyText}>{t('pleaseWait')}</p>
    </div>
  );

  return (
    <div className={styles.dashboard} dir="ltr">

      {/* Header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>{t('dashboard')}</h1>
          <p className={styles.pageSubtitle}>{t('overviewOfMortalityData')}</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          {(quarter || year) && (
            <div style={{ fontSize: 13, fontWeight: 600, color: '#3b82f6', background: '#eff6ff', padding: '4px 12px', borderRadius: 12 }}>
              {quarter} {year}
            </div>
          )}
          <div className={styles.datebadge}>
            {new Date().toLocaleDateString(i18n.language === 'ar' ? 'ar-SA' : 'en-US', { year: 'numeric', month: 'long' })}
          </div>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className={styles.kpiGrid}>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}><span className={styles.kpiIcon}>💀</span><span className={styles.kpiLabel}>{t('totalDeaths')}</span></div>
          <div className={styles.kpiValue}>{stats.totalDeaths.toLocaleString()}</div>
          <div className={styles.kpiFooter} style={{ display: 'flex', flexDirection: 'column', gap: 3, alignItems: 'flex-start' }}>
            <span className={styles.kpiTrend}>KPI-included cases</span>
            <ChangeBadge label="vs prev quarter" current={stats.totalDeaths} previous={prevQuarter?.deaths}     lowerIsBetter={true} />
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}><span className={styles.kpiIcon}>👴</span><span className={styles.kpiLabel}>{t('averageAge')}</span></div>
          <div className={styles.kpiValue}>{stats.averageAge}</div>
          <div className={styles.kpiFooter}><span className={styles.kpiTrend}>{t('years')}</span></div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}><span className={styles.kpiIcon}>🏥</span><span className={styles.kpiLabel}>{t('averageLOS')}</span></div>
          <div className={styles.kpiValue}>{stats.averageLOS}</div>
          <div className={styles.kpiFooter}><span className={styles.kpiTrend}>{t('days')}</span></div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}><span className={styles.kpiIcon}>📈</span><span className={styles.kpiLabel}>Mortality Rate</span></div>
          <div className={styles.kpiValue}>{stats.mortalityRate !== null ? `${stats.mortalityRate.toFixed(2)}%` : '—'}</div>
          <div className={styles.kpiFooter} style={{ display: 'flex', flexDirection: 'column', gap: 3, alignItems: 'flex-start' }}>
            <span className={styles.kpiTrend}>Target: {MORTALITY_TARGET}%</span>
            <ChangeBadge label="vs prev quarter" current={stats.mortalityRate} previous={prevQuarter?.rate}     lowerIsBetter={true} />
          </div>
        </div>

      </div>

{/* ── ROW A — Gauge (25%) + Trend (75%) ── */}
{historyData.length > 0 && (
  <div
    style={{
      display: 'grid',
      gridTemplateColumns: '1fr 3fr',   // 25% | 75%
      gap: 24,
      marginBottom: 24,
      alignItems: 'stretch'
    }}
  >

    {/* ───────── Gauge (25%) ───────── */}
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Current Quarter</h3>
      </div>

      <div
        className={styles.chartBody}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px 0'
        }}
      >
        {stats.mortalityRate !== null ? (
          <MortalityGauge
            rate={stats.mortalityRate}
            target={MORTALITY_TARGET}
          />
        ) : (
          <div style={{ textAlign: 'center', color: '#94a3b8' }}>
            Total Patients not provided
          </div>
        )}
      </div>
    </div>

    {/* ───────── Trend Line (75%) ───────── */}
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>
          Inpatient Mortality Rate vs Target (T &lt; {MORTALITY_TARGET}%)
        </h3>
      </div>

      <div className={styles.chartBody}>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={historyData.map(h => ({
              label: `${h.quarter} ${h.year}`,
              rate: h.rate,
              target: MORTALITY_TARGET
            }))}
            margin={{ top: 16, right: 20, left: 0, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />

            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: '#64748b' }}
              interval={0}
              angle={-30}
              textAnchor="end"
              height={60}
            />

            <YAxis
              tick={{ fontSize: 11 }}
              domain={[
                0,
                Math.max(...historyData.map(h => h.rate), 2) + 0.5
              ]}
              tickFormatter={(v) => `${v}%`}
            />

            <Tooltip {...TS} formatter={(v) => [`${v}%`]} />

            <Legend verticalAlign="top" height={32} />

            <Line
              type="monotone"
              dataKey="rate"
              name="Actual"
              stroke="#2563ea"
              strokeWidth={3}
              dot={{ r: 4 }}
              label={{
              position: 'top',
              fontSize: 10,
              fill: '#3b82f6',
              formatter: (value) => `${value}%`
            }}

            />

            <Line
              type="monotone"
              dataKey="target"
              name="Target"
              stroke="#eb4647"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>

  </div>
)}

      {/* ── ROW B — Building + Entry ── */}
      <div className={styles.chartsGrid}>
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}><h3 className={styles.chartTitle}>Mortality by Building — المبنى</h3></div>
          <div className={styles.chartBody} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24 }}>
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie data={stats.buildingChart} cx="50%" cy="50%" innerRadius={70} outerRadius={120} dataKey="value" labelLine={false} label={PieLabel} startAngle={90} endAngle={-270}>
                  {stats.buildingChart.map((entry,i) => <Cell key={i} fill={BUILDING_COLORS[entry.name]||COLORS[i%COLORS.length]} />)}
                </Pie>
                <Tooltip {...TS} formatter={(v,name) => [`${v} deaths`, name]} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {stats.buildingChart.map((entry,i) => {
                const color = BUILDING_COLORS[entry.name]||COLORS[i%COLORS.length];
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 14 }}>{entry.value}</div>
                    <div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{entry.name}</div>
                      <div style={{ color: '#94a3b8', fontSize: 11 }}>{((entry.value/stats.totalDeaths)*100).toFixed(1)}% of total</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}><h3 className={styles.chartTitle}>Mortality by Entry Type — تصنيف وجهة الدخول</h3></div>
          <div className={styles.chartBody}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.entryChart} margin={{ top: 4, right: 16, left: 0, bottom: 25}}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis   dataKey="name" axisLine={false} tickLine={false} interval={0} angle={-25} textAnchor="end" height={60} tick={{ fontSize: 10, fill: '#64748b' }}/>
                <YAxis hide />
                <Tooltip {...TS} formatter={v => [v, 'Deaths']} />
                <Bar dataKey="count" fill="#2563ea" name="Deaths" radius={[6,6,0,0]}>
                  <LabelList dataKey="count" position="top" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

{/* ── ROW C — Age + Top Causes ── */}
<div className={styles.chartsGrid}>

  {/* ───────── AGE GROUP ───────── */}
  <div className={styles.chartCard}>
    <div className={styles.chartHeader}>
      <h3 className={styles.chartTitle}>
        Mortality by Age Group — تصنيف العمر
      </h3>
    </div>

    <div className={styles.chartBody}>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={stats.ageChart}
          margin={{ top: 20, right: 5, left: 0, bottom: 5 }}
        >

          <XAxis
            dataKey="name"
            axisLine={false}
            tickLine={false}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={60}
            tick={{ fontSize: 10, fill: '#64748b' }}
          />

          <YAxis hide />

          <Tooltip {...TS} formatter={(v) => [v, 'Deaths']} />

          <Bar
            dataKey="count"
            fill="#2563ea"
            radius={[6, 6, 0, 0]}
            maxBarSize={42}
          >
            <LabelList
              dataKey="count"
              position="top"
              style={{ fontSize: 11, fontWeight: 600 }}
            />
          </Bar>

        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>


  {/* ───────── TOP CAUSES ───────── */}
  <div className={styles.chartCard}>
    <div className={styles.chartHeader}>
      <h3 className={styles.chartTitle}>
        {t('topCausesOfDeath')}
      </h3>
    </div>

    <div className={styles.chartBody}>
      <ResponsiveContainer width="100%" height={280}>
  <BarChart
    data={stats.topCauses}
    layout="vertical"
    margin={{ top: 5, right: 5, left: 0, bottom: 5 }}
  >

    {/* Hide numeric axis */}
    <XAxis type="number" hide />

    {/* Reduce Y-axis width so chart shifts right */}
    <YAxis
      type="category"
      dataKey="cause"
      axisLine={false}
      tickLine={false}
      tick={{ fontSize: 12, fill: '#334155', fontWeight: 500 }}
      width={100}
    />

    <Tooltip {...TS} formatter={(v) => [v, 'Deaths']} />

    <Bar
      dataKey="count"
      fill="#2563ea"
      radius={[0, 8, 8, 0]}
      barSize={28}   // ← thicker bars
    >
      <LabelList
        dataKey="count"
        position="right"
        style={{ fontSize: 12, fontWeight: 700 }}
      />
    </Bar>

  </BarChart>
</ResponsiveContainer>
    </div>
  </div>

</div>

{/* ── ROW D — Nursing Department (Integrated Table + True Bar Chart Scaling) ── */}
<div className={styles.chartCard} style={{ marginBottom: '1.5rem' }}>

  <div className={styles.chartHeader}>
    <h3 className={styles.chartTitle}>
      Mortality by Nursing Department — القسم التمريضي
    </h3>
  </div>

  <div style={{ padding: '0 20px 20px' }}>

    {/*
      Compute max department count so bars scale
      relative to the largest department (true bar behavior)
    */}
    {(() => {
      const maxDeptCount = Math.max(...stats.deptChart.map(d => d.count));

      return (
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: 13,
            tableLayout: 'fixed'
          }}
        >

          <colgroup>
            <col style={{ width: '6%' }} />
            <col style={{ width: '34%' }} />
            <col style={{ width: '12%' }} />
            <col style={{ width: '48%' }} />
          </colgroup>

          <thead>
            <tr style={{ background: '#f8fafc' }}>
              <th style={TH}>#</th>
              <th style={TH}>Department</th>
              <th style={{ ...TH, textAlign: 'left' }}>Deaths</th>
              <th style={TH}>Share</th>
            </tr>
          </thead>

          <tbody>
            {stats.deptChart.map((row, i) => {

              const widthPct = (row.count / maxDeptCount) * 100;
              const sharePct = (row.count / stats.totalDeaths) * 100;

              return (
                <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>

                  {/* Rank */}
                  <td style={TD}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 26,
                        height: 26,
                        borderRadius: 6,
                        background: row.color,
                        color: '#fff',
                        fontSize: 12,
                        fontWeight: 700
                      }}
                    >
                      {i + 1}
                    </span>
                  </td>

                  {/* Department */}
                  <td style={{ ...TD, fontWeight: 600, color: '#1e293b' }}>
                    {row.dept}
                  </td>

                  {/* Deaths */}
                  <td
                    style={{
                      ...TD,
                      fontWeight: 700,
                      color: '#1e293b',
                      textAlign: 'left'
                    }}
                  >
                    {row.count}
                  </td>

                  {/* Share + True Bar */}
                  <td style={TD}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12
                      }}
                    >

                      {/* Background track */}
                      <div
                        style={{
                          flex: 1,
                          height: 18,
                          borderRadius: 10,
                          background: '#e2e8f0',
                          overflow: 'hidden',
                          position: 'relative'
                        }}
                      >

                        {/* Scaled bar */}
                        <div
                          style={{
                            width: `${widthPct}%`,
                            height: '100%',
                            background: row.color,
                            borderRadius: 10,
                            transition: 'width 0.6s ease'
                          }}
                        />

                      </div>

                      {/* Share Percentage */}
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: '#475569',
                          minWidth: 48,
                          textAlign: 'right'
                        }}
                      >
                        {sharePct.toFixed(1)}%
                      </span>

                    </div>
                  </td>

                </tr>
              );
            })}

            {/* Total Row */}
            <tr
              style={{
                background: '#f8fafc',
                fontWeight: 700,
                borderTop: '2px solid #e2e8f0'
              }}
            >
              <td colSpan={2} style={{ ...TD, color: '#1e293b' }}>
                Total
              </td>
              <td style={{ ...TD, textAlign: 'left', color: '#1e293b' }}>
                {stats.totalDeaths}
              </td>
              <td style={{ ...TD, color: '#1e293b' }}>
                100%
              </td>
            </tr>

          </tbody>
        </table>
      );
    })()}

  </div>
</div>
      {/* ── ROW E — WHO Pareto ── */}
    {/* ── ROW E — WHO Pareto (Executive Large Version) ── */}
<div className={styles.chartCard} style={{ marginBottom: '1.5rem' }}>

  <div className={styles.chartHeader}>
    <h3 className={styles.chartTitle}>
      Mortality by WHO Category 1 — Pareto
    </h3>
  </div>

  <div style={{ padding: '0 20px 30px' }}>

    {(() => {

      const data = stats.whoChart.map(row => ({
        ...row,
        pct: (row.count / stats.totalDeaths) * 100
      }));

      return (
        <ResponsiveContainer width="100%" height={550}>
  <ComposedChart
    data={stats.whoChart}
    margin={{ top: 50, right: 40, left: 50, bottom: 50 }}
  >

    {/* Soft horizontal grid */}
    <CartesianGrid
      strokeDasharray="3 3"
      vertical={false}
      stroke="#f1f5f9"
    />

    {/* X Axis (bigger & cleaner) */}
    <XAxis
      dataKey="cat"
      interval={0}
      angle={-25}
      textAnchor="end"
      height={100}
      tick={{
        fontSize: 13,
        fontWeight: 600,
        fill: "#334155"
      }}
      axisLine={false}
      tickLine={false}
    />

    {/* Hidden axes (logic preserved) */}
    <YAxis yAxisId="left" hide />
    <YAxis yAxisId="right" orientation="right" domain={[0, 100]} hide />

    <Tooltip
      formatter={(value, name) =>
        name === "Cumulative"
          ? [`${value}%`, "Cumulative %"]
          : [value, "Deaths"]
      }
    />

    {/* Bars — Premium Blue */}
    <Bar
      yAxisId="left"
      dataKey="count"
      radius={[10, 10, 0, 0]}
      barSize={62}
      fill="#2563eb"
      label={{
        position: "top",
        fontSize: 12,
        fontWeight: 600,
        fill: "#1e293b",
        formatter: (value, entry) => {
          const pct = ((value / stats.totalDeaths) * 100).toFixed(1);
          return `${value}`;
        }
      }}
    />

    {/* Cumulative Line — Premium Orange */}
    <Line
      yAxisId="right"
      type="monotone"
      dataKey="cumPct"
      stroke="#6784a2"
      strokeWidth={3.5}
      dot={{
        r: 5,
        strokeWidth: 2,
        fill: "#fff"
      }}
      activeDot={{ r: 7 }}
      name="Cumulative"
      label={{
        position: "top",
        fontSize: 12,
        fontWeight: 600,
        fill: "#6784a2",
        formatter: (v) => `${v}%`
      }}
    />

  </ComposedChart>
</ResponsiveContainer>
      );
    })()}

  </div>
</div>



      {/* ── ROW F — Historical Comparisons ── */}
      <HistoricalComparisonsSection
      allThisYear={allThisYear}
      currentQShort={currentQShort}
      stats={stats}
      styles={styles}
    />



    </div>
  );
}

export default Dashboard;
