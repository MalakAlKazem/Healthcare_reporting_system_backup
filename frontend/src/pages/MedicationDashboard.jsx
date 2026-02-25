import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/Dashboard.module.css';

import {
  LineChart, Line,
  AreaChart, Area,
  BarChart, Bar,
  ComposedChart,
  PieChart, Pie, Cell, Sector,
  XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

// ─── RTL/LTR + Font fix ───────────────────────────────────────────────────────
// Forces the entire dashboard to render LTR regardless of the app's language dir.
// Also prevents Arabic font fallback from synthesising fake bold (causes "thick" text).
const FONT_FIX_STYLE = `
  .med-dashboard,
  .med-dashboard * {
    direction: ltr !important;
    unicode-bidi: isolate;
    font-synthesis: none !important;
    -webkit-font-smoothing: antialiased;
    font-weight: inherit;
  }
  .med-dashboard h1,
  .med-dashboard h2,
  .med-dashboard h3 {
    font-weight: 700;
  }
  .med-dashboard .kpi-value {
    font-weight: 800;
  }
  /* Arabic text nodes still render correctly — only layout direction is forced LTR */
`;

// ─── Design Tokens ────────────────────────────────────────────────────────────
const BLUE        = '#2563eb';
const BLUE_LIGHT  = '#eff6ff';
const GREEN       = '#10b981';
const AMBER       = '#f59e0b';
const RED         = '#ef4444';
const SLATE       = '#64748b';
const SLATE_LIGHT = '#f8fafc';
const BORDER      = '#e2e8f0';
const PALETTE     = ['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316','#14b8a6','#ec4899','#84cc16'];

// ─── Shared Tooltip ───────────────────────────────────────────────────────────
const TS = {
  contentStyle: {
    background: '#fff', border: `1px solid ${BORDER}`, borderRadius: 12,
    padding: '10px 14px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)', fontSize: 12,
  },
};

// ─── Table styles ─────────────────────────────────────────────────────────────
const TH_STYLE = {
  padding: '10px 12px', textAlign: 'left', fontWeight: 700, color: SLATE,
  fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em',
  borderBottom: `2px solid ${BORDER}`, whiteSpace: 'nowrap', background: SLATE_LIGHT,
};
const TD_STYLE = { padding: '9px 12px', color: '#475569', verticalAlign: 'middle' };

// ─── Section ──────────────────────────────────────────────────────────────────
function Section({ title, icon, children }) {
  return (
    <div style={{ marginBottom: 36, direction: 'ltr' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, direction: 'ltr' }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: '#1e293b', margin: 0 }}>{title}</h2>
        <div style={{ flex: 1, height: 1, background: BORDER }} />
      </div>
      {children}
    </div>
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────
function Card({ children, style = {} }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 14, border: `1px solid ${BORDER}`,
      boxShadow: '0 1px 8px rgba(0,0,0,0.04)', overflow: 'hidden', direction: 'ltr', ...style,
    }}>
      {children}
    </div>
  );
}
function CardHeader({ title, badge }) {
  return (
    <div style={{ padding: '14px 18px', borderBottom: `1px solid ${BORDER}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', direction: 'ltr' }}>
      <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#1e293b' }}>{title}</h3>
      {badge && <span style={{ fontSize: 11, color: SLATE, background: SLATE_LIGHT, padding: '3px 10px', borderRadius: 20, fontWeight: 600 }}>{badge}</span>}
    </div>
  );
}
function CardBody({ children, style = {} }) {
  return <div style={{ padding: '14px 16px', ...style }}>{children}</div>;
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ icon, label, value, valueColor, sub, badge, badgeColor, badgeBg }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 14, border: `1px solid ${BORDER}`,
      boxShadow: '0 1px 8px rgba(0,0,0,0.04)', padding: '20px 22px',
      display: 'flex', flexDirection: 'column', gap: 6, direction: 'ltr',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
        <span style={{ fontSize: 11, fontWeight: 600, color: SLATE, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      </div>
      <div style={{ fontSize: 34, fontWeight: 800, color: valueColor || '#1e293b', lineHeight: 1.1 }}>{value}</div>
      {badge && (
        <div style={{ display: 'inline-flex', alignItems: 'center', background: badgeBg || BLUE_LIGHT, color: badgeColor || BLUE, borderRadius: 20, padding: '3px 10px', fontSize: 11, fontWeight: 700, alignSelf: 'flex-start' }}>
          {badge}
        </div>
      )}
      {sub && <div style={{ fontSize: 11, color: SLATE }}>{sub}</div>}
    </div>
  );
}

// ─── Semicircle Gauge ─────────────────────────────────────────────────────────
function MedicationGauge({ rate, target }) {
  const MAX     = Math.max(rate * 1.5, target * 2, 0.05);
  const ratePct = Math.min(rate, MAX) / MAX;
  const tgtPct  = Math.min(target, MAX) / MAX;
  const isAbove = rate > target;
  const arc = (pct, radius) => {
    const a = Math.PI * pct;
    return `M ${100 - radius} 100 A ${radius} ${radius} 0 ${pct > 0.5 ? 1 : 0} 1 ${100 - radius * Math.cos(a)} ${100 - radius * Math.sin(a)}`;
  };
  return (
    <div style={{ textAlign: 'center', padding: '8px 0' }}>
      <svg viewBox="0 0 200 115" width="100%" style={{ maxWidth: 300 }}>
        <path d={arc(1, 70)} fill="none" stroke={BORDER} strokeWidth="16" strokeLinecap="round" />
        <path d={arc(ratePct, 70)} fill="none" stroke={isAbove ? RED : GREEN} strokeWidth="14" strokeLinecap="round" />
        <line x1={100 - 62 * Math.cos(Math.PI * tgtPct)} y1={100 - 62 * Math.sin(Math.PI * tgtPct)}
          x2={100 - 80 * Math.cos(Math.PI * tgtPct)} y2={100 - 80 * Math.sin(Math.PI * tgtPct)}
          stroke={AMBER} strokeWidth="4" strokeLinecap="round" />
        <text x="100" y="82" textAnchor="middle" fontSize="22" fontWeight="800" fill={isAbove ? RED : GREEN}>{rate.toFixed(4)}%</text>
        <text x="100" y="98" textAnchor="middle" fontSize="10" fill="#94a3b8">target {target}%</text>
      </svg>
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: isAbove ? '#fef2f2' : '#f0fdf4', color: isAbove ? '#dc2626' : '#16a34a', borderRadius: 20, padding: '5px 16px', fontSize: 12, fontWeight: 700, marginTop: 6 }}>
        {isAbove ? '▲ Above Target' : '▼ Below Target'}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 14, fontSize: 12, color: SLATE }}>
        {[
          { label: 'Actual', value: `${rate.toFixed(4)}%`, color: isAbove ? RED : GREEN },
          { label: 'Target', value: `${target}%`, color: AMBER },
          { label: isAbove ? 'Over' : 'Under', value: `${Math.abs(rate - target).toFixed(4)}%`, color: isAbove ? RED : GREEN },
        ].map((item, i, arr) => (
          <React.Fragment key={item.label}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: item.color }}>{item.value}</div>
              <div style={{ marginTop: 2 }}>{item.label}</div>
            </div>
            {i < arr.length - 1 && <div style={{ width: 1, background: BORDER }} />}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// ─── Advanced Donut Chart ─────────────────────────────────────────────────────
// Active slice expands on hover; custom external label lines; inner value
const renderActiveShape = (props) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
  return (
    <g>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius - 4} outerRadius={outerRadius + 10}
        startAngle={startAngle} endAngle={endAngle} fill={fill} opacity={0.95} />
      <Sector cx={cx} cy={cy} innerRadius={outerRadius + 14} outerRadius={outerRadius + 18}
        startAngle={startAngle} endAngle={endAngle} fill={fill} />
    </g>
  );
};

const renderCustomLabel = ({ cx, cy, midAngle, outerRadius, percent, name, value }) => {
  if (percent < 0.04) return null;
  const RADIAN = Math.PI / 180;
  const radius = outerRadius + 32;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  const lx1 = cx + (outerRadius + 6) * Math.cos(-midAngle * RADIAN);
  const ly1 = cy + (outerRadius + 6) * Math.sin(-midAngle * RADIAN);
  const lx2 = cx + (outerRadius + 22) * Math.cos(-midAngle * RADIAN);
  const ly2 = cy + (outerRadius + 22) * Math.sin(-midAngle * RADIAN);
  return (
    <g>
      <line x1={lx1} y1={ly1} x2={lx2} y2={ly2} stroke="#94a3b8" strokeWidth={1} />
      <text x={x} y={y - 5} textAnchor={x > cx ? 'start' : 'end'} fill="#1e293b" fontSize={11} fontWeight={600}>{name}</text>
      <text x={x} y={y + 9} textAnchor={x > cx ? 'start' : 'end'} fill={SLATE} fontSize={10}>{value} ({(percent * 100).toFixed(0)}%)</text>
    </g>
  );
};

function AdvancedDonut({ data, centerValue, centerLabel, height = 360 }) {
  const [activeIdx, setActiveIdx] = useState(0);
  return (
    <div style={{ position: 'relative' }}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart margin={{ top: 20, right: 40, bottom: 20, left: 40 }}>
          <Pie
            data={data} dataKey="value" nameKey="name"
            cx="50%" cy="46%"
            innerRadius="38%" outerRadius="58%"
            startAngle={90} endAngle={-270}
            activeIndex={activeIdx}
            activeShape={renderActiveShape}
            onMouseEnter={(_, i) => setActiveIdx(i)}
            label={renderCustomLabel}
            labelLine={false}
            isAnimationActive={false}
          >
            {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
          </Pie>
          <Tooltip {...TS} formatter={v => [`${v} errors`]} />
        </PieChart>
      </ResponsiveContainer>
      {/* Center label */}
      {centerValue !== undefined && (
        <div style={{ position: 'absolute', top: '42%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none' }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#1e293b', lineHeight: 1 }}>{centerValue}</div>
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>{centerLabel}</div>
        </div>
      )}
      {/* Colored legend dots */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 16px', justifyContent: 'center', marginTop: 8, padding: '0 8px' }}>
        {data.map((d, i) => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer', opacity: activeIdx === i ? 1 : 0.6 }}
            onMouseEnter={() => setActiveIdx(i)}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: PALETTE[i % PALETTE.length], flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: '#334155', fontWeight: activeIdx === i ? 700 : 400 }}>{d.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Horizontal Bar Chart ─────────────────────────────────────────────────────
function HBarChart({ data, dataKey, nameKey, color = BLUE }) {
  return (
    <div dir="ltr">
      <ResponsiveContainer width="100%" height={Math.max(260, data.length * 46)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, left: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
          <XAxis type="number" hide />
          <YAxis type="category" dataKey={nameKey} width={130} tick={{ fontSize: 11, fill: '#334155' }} />
          <Tooltip {...TS} formatter={v => [`${v} errors`]} />
          <Bar dataKey={dataKey} fill={color} radius={[0, 7, 7, 0]} barSize={20}
            label={{ position: 'right', fontSize: 12, fontWeight: 700, fill: '#1e293b' }} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Department Table ─────────────────────────────────────────────────────────
function DeptTable({ deptData, totalErrors, ar }) {
  const max = Math.max(...deptData.map(d => d.count), 1);
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
      <thead>
        <tr>
          <th style={{ ...TH_STYLE, width: '5%' }}>#</th>
          <th style={{ ...TH_STYLE, width: '36%' }}>{ar ? 'القسم' : 'Department'}</th>
          <th style={{ ...TH_STYLE, width: '10%', textAlign: 'center' }}>{ar ? 'الأخطاء' : 'Errors'}</th>
          <th style={{ ...TH_STYLE, width: '49%' }}>{ar ? 'النسبة' : 'Share'}</th>
        </tr>
      </thead>
      <tbody>
        {deptData.map((row, i) => {
          const pct = (row.count / totalErrors) * 100;
          const color = PALETTE[i % PALETTE.length];
          return (
            <tr key={i} style={{ borderBottom: '1px solid #f8fafc' }}>
              <td style={TD_STYLE}><span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 22, height: 22, borderRadius: 5, background: color, color: '#fff', fontSize: 10, fontWeight: 700 }}>{i + 1}</span></td>
              <td style={{ ...TD_STYLE, fontWeight: 600, color: '#1e293b' }}>{row.dept}</td>
              <td style={{ ...TD_STYLE, fontWeight: 700, textAlign: 'center' }}>{row.count}</td>
              <td style={TD_STYLE}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ flex: 1, height: 7, borderRadius: 4, background: '#f1f5f9', overflow: 'hidden' }}>
                    <div style={{ width: `${(row.count / max) * 100}%`, height: '100%', background: color, borderRadius: 4 }} />
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 600, minWidth: 40, textAlign: 'right', color: SLATE }}>{pct.toFixed(1)}%</span>
                </div>
              </td>
            </tr>
          );
        })}
        <tr style={{ background: SLATE_LIGHT, fontWeight: 700, borderTop: `2px solid ${BORDER}` }}>
          <td colSpan={2} style={{ ...TD_STYLE, color: '#1e293b' }}>{ar ? 'الإجمالي' : 'Total'}</td>
          <td style={{ ...TD_STYLE, color: '#1e293b', textAlign: 'center' }}>{totalErrors}</td>
          <td style={{ ...TD_STYLE, color: '#1e293b' }}>100%</td>
        </tr>
      </tbody>
    </table>
  );
}

// ─── Cause Distribution ───────────────────────────────────────────────────────
function CauseDistributionChart({ data }) {
  const total  = data.reduce((s, d) => s + d.count, 0);
  const sorted = [...data].sort((a, b) => b.count - a.count);
  const max    = sorted[0]?.count || 1;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
      {sorted.map((item, i) => {
        const pct   = (item.count / total) * 100;
        const color = PALETTE[i % PALETTE.length];
        return (
          <div key={item.cause} style={{ display: 'grid', gridTemplateColumns: '200px 1fr 52px 46px', alignItems: 'center', gap: 10 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#334155', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={item.cause}>{item.cause}</div>
            <div style={{ height: 22, background: '#f1f5f9', borderRadius: 5, overflow: 'hidden' }}>
              <div style={{ width: `${(item.count / max) * 100}%`, height: '100%', background: color, borderRadius: 5 }} />
            </div>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#1e293b', textAlign: 'right' }}>{item.count}</div>
            <div style={{ fontSize: 11, fontWeight: 600, color: SLATE, textAlign: 'right' }}>{pct.toFixed(1)}%</div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Heatmap ──────────────────────────────────────────────────────────────────
// rows/cols are label arrays; matrix is { rowKey: { colKey: number } }
function Heatmap({ rows, cols, matrix, rowLabel, colLabel }) {
  const allVals = rows.flatMap(r => cols.map(c => matrix[r]?.[c] ?? 0));
  const max     = Math.max(...allVals, 1);

  const cellBg = (val) => {
    const t = val / max;
    // white → deep blue
    const r = Math.round(255 - t * (255 - 37));
    const g = Math.round(255 - t * (255 - 99));
    const b = Math.round(255 - t * (255 - 235));
    return `rgb(${r},${g},${b})`;
  };
  const cellFg = (val) => (val / max) > 0.45 ? '#fff' : '#1e293b';

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 11, width: '100%' }}>
        <thead>
          <tr>
            <th style={{ padding: '9px 12px', background: SLATE_LIGHT, borderBottom: `2px solid ${BORDER}`, borderRight: `2px solid ${BORDER}`, fontSize: 11, color: SLATE, fontWeight: 700, textAlign: 'left', minWidth: 130 }}>
              {rowLabel} ╲ {colLabel}
            </th>
            {cols.map(col => (
              <th key={col} style={{ padding: '9px 10px', background: SLATE_LIGHT, borderBottom: `2px solid ${BORDER}`, borderRight: `1px solid ${BORDER}`, fontSize: 10, color: SLATE, fontWeight: 700, textAlign: 'center', whiteSpace: 'nowrap', minWidth: 80 }}>
                {col}
              </th>
            ))}
            <th style={{ padding: '9px 10px', background: '#dbeafe', borderBottom: `2px solid ${BORDER}`, fontSize: 11, color: BLUE, fontWeight: 800, textAlign: 'center', minWidth: 60 }}>Σ</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => {
            const rowTotal = cols.reduce((s, c) => s + (matrix[row]?.[c] ?? 0), 0);
            return (
              <tr key={row}>
                <td style={{ padding: '9px 12px', fontWeight: 700, color: '#1e293b', borderBottom: `1px solid ${BORDER}`, borderRight: `2px solid ${BORDER}`, background: SLATE_LIGHT, fontSize: 11, whiteSpace: 'nowrap' }}>{row}</td>
                {cols.map(col => {
                  const val = matrix[row]?.[col] ?? 0;
                  return (
                    <td key={col} title={`${row} × ${col}: ${val}`}
                      style={{ padding: '9px 10px', textAlign: 'center', fontWeight: val > 0 ? 700 : 400, fontSize: 12, borderBottom: `1px solid ${BORDER}`, borderRight: `1px solid ${BORDER}`, background: val > 0 ? cellBg(val) : '#fafafa', color: val > 0 ? cellFg(val) : '#cbd5e1', minWidth: 80 }}>
                      {val > 0 ? val : '—'}
                    </td>
                  );
                })}
                <td style={{ padding: '9px 10px', textAlign: 'center', fontWeight: 800, fontSize: 12, borderBottom: `1px solid ${BORDER}`, background: '#dbeafe', color: BLUE }}>{rowTotal}</td>
              </tr>
            );
          })}
          <tr style={{ background: '#dbeafe' }}>
            <td style={{ padding: '9px 12px', fontWeight: 800, color: BLUE, borderTop: `2px solid ${BORDER}`, borderRight: `2px solid ${BORDER}`, fontSize: 11 }}>Σ Total</td>
            {cols.map(col => {
              const colTotal = rows.reduce((s, r) => s + (matrix[r]?.[col] ?? 0), 0);
              return <td key={col} style={{ padding: '9px 10px', textAlign: 'center', fontWeight: 800, fontSize: 12, borderTop: `2px solid ${BORDER}`, borderRight: `1px solid ${BORDER}`, color: BLUE }}>{colTotal || '—'}</td>;
            })}
            <td style={{ padding: '9px 10px', textAlign: 'center', fontWeight: 800, fontSize: 12, borderTop: `2px solid ${BORDER}`, color: BLUE, background: '#bfdbfe' }}>
              {rows.reduce((s, r) => s + cols.reduce((ss, c) => ss + (matrix[r]?.[c] ?? 0), 0), 0)}
            </td>
          </tr>
        </tbody>
      </table>
      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12, fontSize: 10, color: SLATE }}>
        <span>Low</span>
        <div style={{ display: 'flex', gap: 2 }}>
          {[0.05, 0.2, 0.4, 0.6, 0.8, 1.0].map((v, i) => (
            <div key={i} style={{ width: 26, height: 12, borderRadius: 2, background: cellBg(v * max) }} />
          ))}
        </div>
        <span>High</span>
        <span style={{ marginLeft: 8, color: '#94a3b8' }}>— = no errors recorded</span>
      </div>
    </div>
  );
}

// ─── Quarter sort ─────────────────────────────────────────────────────────────
const Q_ORDER = { 'الفصل الاول': 1, 'الفصل الأول': 1, 'الفصل الثاني': 2, 'الفصل الثالث': 3, 'الفصل الرابع': 4 };
const sortQuarters = arr => [...arr].sort((a, b) =>
  (parseInt(a.year) * 10 + (Q_ORDER[a.quarter] || 0)) - (parseInt(b.year) * 10 + (Q_ORDER[b.quarter] || 0))
);

// ─── Build cross-tab matrix from two flat dicts ───────────────────────────────
// If the backend provides heatmap_cycle_cause use it directly.
// Otherwise approximate: distribute proportionally using both flat distributions.
// This gives a plausible matrix until the backend supplies real cross-tab data.
function buildCrossTab(rowDict, colDict) {
  const rows   = Object.keys(rowDict).filter(k => rowDict[k] > 0);
  const cols   = Object.keys(colDict).filter(k => colDict[k] > 0);
  const total  = Object.values(rowDict).reduce((s, v) => s + v, 0);
  const matrix = {};
  rows.forEach(r => {
    matrix[r] = {};
    cols.forEach(c => {
      // Distribute using joint probability approximation
      const approx = total > 0 ? Math.round((rowDict[r] * colDict[c]) / total) : 0;
      matrix[r][c] = approx;
    });
  });
  return { matrix, rows, cols };
}

// ═════════════════════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ═════════════════════════════════════════════════════════════════════════════
function MedicationDashboard({ language }) {
  const navigate = useNavigate();
  const ar = language === 'ar';
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const TARGET = 0.03;

  useEffect(() => {
    fetch('http://localhost:8000/api/medication/history')
      .then(r => r.json())
      .then(result => { setData(result); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  }, []);

  if (loading) return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>⏳</div>
      <h2 className={styles.emptyTitle}>Loading...</h2>
    </div>
  );
  if (!data || !Array.isArray(data) || data.length === 0) return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>💊</div>
      <h2 className={styles.emptyTitle}>No Data Available</h2>
      <button onClick={() => navigate('/medication/upload')} className={styles.uploadButton}>Upload Data</button>
    </div>
  );

  const sorted  = sortQuarters(data);
  const current = sorted[sorted.length - 1];

  // ── Flat distributions ─────────────────────────────────────────────────────
  const cycleData = Object.entries(current.error_cycle || {})
    .map(([name, value]) => ({ name, value: Number(value) }))
    .filter(d => d.value > 0).sort((a, b) => b.value - a.value);

  const detectedData = Object.entries(current.detected_by || {})
    .map(([name, value]) => ({ name, value: Number(value) }))
    .filter(d => d.value > 0).sort((a, b) => b.value - a.value);

  const shiftData = Object.entries(current.duty_shift || {})
    .map(([name, value]) => ({ name, value: Number(value) }))
    .filter(d => d.value > 0);

  const staffData = Object.entries(current.staff_involved || {})
    .map(([name, value]) => ({ name, value: Number(value) }))
    .filter(d => d.value > 0).sort((a, b) => b.value - a.value);

  const deptData = Object.entries(current.departments || {})
    .map(([dept, count]) => ({ dept, count: Number(count) }))
    .filter(d => d.count > 0).sort((a, b) => b.count - a.count);
  const totalDeptErrors = deptData.reduce((s, d) => s + d.count, 0);

  const causesData = Object.entries(current.error_causes || {})
    .map(([cause, count]) => ({ cause, count: Number(count) }))
    .filter(d => d.count > 0).sort((a, b) => b.count - a.count);
  const totalCauses = causesData.reduce((s, d) => s + d.count, 0);

  // ── Pareto ─────────────────────────────────────────────────────────────────
  let cum = 0;
  const paretoData = causesData.map(item => {
    cum += item.count;
    return { ...item, cumPct: Number(((cum / totalCauses) * 100).toFixed(1)) };
  });

  // ── Heatmaps ───────────────────────────────────────────────────────────────
  // Use real cross-tab from backend if available; otherwise approximate
  const cycleCauseRaw = current.heatmap_cycle_cause;
  const causeCycleRaw = current.heatmap_cause_cycle;

  const cycleDict = Object.fromEntries(cycleData.map(d => [d.name, d.value]));
  const causeDict = Object.fromEntries(causesData.map(d => [d.cause, d.count]));

  const { matrix: hm1, rows: hm1rows, cols: hm1cols } = cycleCauseRaw
    ? { matrix: cycleCauseRaw, rows: Object.keys(cycleCauseRaw), cols: Array.from(new Set(Object.values(cycleCauseRaw).flatMap(Object.keys))) }
    : buildCrossTab(cycleDict, causeDict);

  const { matrix: hm2, rows: hm2rows, cols: hm2cols } = causeCycleRaw
    ? { matrix: causeCycleRaw, rows: Object.keys(causeCycleRaw), cols: Array.from(new Set(Object.values(causeCycleRaw).flatMap(Object.keys))) }
    : buildCrossTab(causeDict, cycleDict);

  // ── Trend data (ALL quarters) ──────────────────────────────────────────────
  const trendData = sorted.map(q => ({
    label: `${q.quarter} ${q.year}`,
    rate: q.error_rate,
    errors: q.total_errors,
    target: TARGET,
  }));

  return (
    <>
      {/* ── Font weight fix: inject once into <head> ── */}
      <style>{FONT_FIX_STYLE}</style>

      <div className={`${styles.dashboard} med-dashboard`} dir="ltr" style={{ padding: '20px', maxWidth: 1600, margin: '0 auto', direction: 'ltr' }}>

        {/* PAGE HEADER */}
        <div style={{ marginBottom: 28, paddingBottom: 20, borderBottom: `1px solid ${BORDER}` }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', direction: 'ltr' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: BLUE_LIGHT, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>💊</div>
              <div>
                <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
                  {ar ? 'لوحة بيانات أخطاء الدواء' : 'Medication Error Dashboard'}
                </h1>
                <p style={{ margin: 0, fontSize: 13, color: SLATE, marginTop: 2 }}>
                  {ar ? 'نظرة عامة على الأداء' : 'Quarterly performance overview & trend analysis'}
                </p>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: BLUE, background: BLUE_LIGHT, padding: '6px 14px', borderRadius: 10 }}>
                {current.quarter} {current.year}
              </div>
              <div style={{ fontSize: 11, color: SLATE, marginTop: 4 }}>Current Quarter</div>
            </div>
          </div>
        </div>

        {/* ═══ SECTION 1 — KPIs ═══ */}
        <Section title={ar ? 'مؤشرات الأداء الرئيسية' : 'Key Performance Indicators'} icon="📊">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, direction: 'ltr' }}>
            <KpiCard icon="💊" label={ar ? 'إجمالي الأخطاء' : 'Total Errors'} value={current.total_errors.toLocaleString()}
              badge={`Q${Q_ORDER[current.quarter] || '?'} ${current.year}`} />
            <KpiCard icon="📈" label={ar ? 'نسبة الخطأ' : 'Error Rate'} value={`${current.error_rate.toFixed(4)}%`}
              valueColor={current.error_rate > TARGET ? RED : GREEN}
              badge={current.error_rate > TARGET ? '▲ Above Target' : '▼ Below Target'}
              badgeColor={current.error_rate > TARGET ? '#dc2626' : '#16a34a'}
              badgeBg={current.error_rate > TARGET ? '#fef2f2' : '#f0fdf4'} />
            <KpiCard icon="💉" label={ar ? 'إجمالي الجرعات' : 'Total Doses'} value={current.total_doses.toLocaleString()} sub="Administered this quarter" />
            <KpiCard icon="🎯" label={ar ? 'المستهدف' : 'Target Rate'} value={`${TARGET}%`} badge="Clinical Standard" badgeColor={AMBER} badgeBg="#fffbeb" />
          </div>
        </Section>

        {/* ═══ SECTION 2 — CURRENT QUARTER PERFORMANCE ═══ */}
        <Section title={ar ? 'أداء الربع الحالي' : 'Current Quarter Performance'} icon="🎯">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16, direction: 'ltr' }}>
            <Card>
              <CardHeader title={ar ? 'مقياس الأداء' : 'Performance Gauge'} badge={`Target: ${TARGET}%`} />
              <CardBody>
                <MedicationGauge rate={current.error_rate} target={TARGET} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader title={ar ? 'اتجاه نسبة الخطأ مقابل الهدف' : 'Error Rate vs Target — All Quarters'} />
              <CardBody style={{ padding: '12px 8px 8px' }}>
                <div dir="ltr">
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={trendData} margin={{ top: 24, right: 16, left: 0, bottom: 44 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                      <XAxis dataKey="label" interval={0} angle={-30} textAnchor="end" height={60} tick={{ fontSize: 10, fill: '#64748b' }} />
                      <YAxis hide domain={[0, Math.max(...sorted.map(q => q.error_rate), TARGET) * 1.4]} />
                      <Tooltip {...TS} formatter={v => [`${v.toFixed(4)}%`]} />
                      <Legend verticalAlign="top" height={28} />
                      <Line type="monotone" dataKey="rate" name="Actual" stroke={BLUE} strokeWidth={2.5}
                        dot={{ r: 4, fill: BLUE }}
                        label={{ position: 'top', fontSize: 10, fontWeight: 700, fill: BLUE, formatter: v => `${v.toFixed(4)}%` }} />
                      <Line type="monotone" dataKey="target" name="Target" stroke={RED} strokeDasharray="6 3" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>
          </div>
        </Section>

        {/* ═══ SECTION 3 — CAUSE DISTRIBUTION ═══ */}
        <Section title={ar ? 'توزيع أسباب الأخطاء' : 'Error Cause Distribution'} icon="🔎">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, direction: 'ltr' }}>
            <Card>
              <CardHeader title={ar ? 'توزيع أسباب الأخطاء' : 'Cause of Error — Distribution'} badge={`${causesData.length} causes`} />
              <CardBody>
                {causesData.length === 0
                  ? <div style={{ color: SLATE }}>No cause data available</div>
                  : <CauseDistributionChart data={causesData} />}
              </CardBody>
            </Card>
            <Card>
              <CardHeader title={ar ? 'تحليل باريتو — أسباب الأخطاء' : 'Pareto Analysis — Error Causes'} badge="80/20 Rule" />
              <CardBody style={{ padding: '12px 8px 8px' }}>
                {paretoData.length === 0
                  ? <div style={{ color: SLATE }}>No data available</div>
                  : (
                    <div dir="ltr">
                      <ResponsiveContainer width="100%" height={380}>
                        <ComposedChart data={paretoData} margin={{ top: 20, right: 44, left: 8, bottom: 80 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                          <XAxis dataKey="cause" interval={0} angle={-35} textAnchor="end" height={90} tick={{ fontSize: 10, fill: '#64748b' }} />
                          <YAxis yAxisId="left" allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                          <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11, fill: AMBER }} width={38} />
                          <Tooltip {...TS} formatter={(v, name) => name === 'Cumulative %' ? [`${v}%`, name] : [v, 'Errors']} />
                          <Legend verticalAlign="top" height={30} />
                          <Bar yAxisId="left" dataKey="count" name="Errors" fill={BLUE} radius={[5, 5, 0, 0]} barSize={34} />
                          <Line yAxisId="right" type="monotone" dataKey="cumPct" name="Cumulative %" stroke={RED} strokeWidth={2.5} dot={{ r: 4, fill: RED }} activeDot={{ r: 6 }} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  )}
              </CardBody>
            </Card>
          </div>
        </Section>

        {/* ═══ SECTION 4 — HEATMAPS ═══ */}
        <Section title={ar ? 'تحليل المصفوفة الحرارية' : 'Cross-Analysis Heatmaps'} icon="🌡️">

          {/* Approximation notice when no real cross-tab from backend */}
          {!current.heatmap_cycle_cause && (
            <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 10, padding: '10px 16px', marginBottom: 16, fontSize: 12, color: '#92400e', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <span style={{ flexShrink: 0 }}>⚠️</span>
              <span>
                Showing <strong>approximated values</strong> based on individual distributions.
                For exact counts, add <code style={{ background: '#fef3c7', padding: '1px 5px', borderRadius: 3 }}>heatmap_cycle_cause</code> and <code style={{ background: '#fef3c7', padding: '1px 5px', borderRadius: 3 }}>heatmap_cause_cycle</code> to your API response.
              </span>
            </div>
          )}

          <Card style={{ marginBottom: 16 }}>
            <CardHeader title={ar ? 'مرحلة العملية × سبب الخطأ' : 'Process Stage × Cause of Error'} badge="Rows = Process | Cols = Cause" />
            <CardBody style={{ padding: '14px 12px' }}>
              {hm1rows.length === 0
                ? <div style={{ color: SLATE }}>No data available.</div>
                : <Heatmap rows={hm1rows} cols={hm1cols} matrix={hm1} rowLabel="Process" colLabel="Cause" />}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title={ar ? 'سبب الخطأ × مرحلة العملية' : 'Cause of Error × Process Stage'} badge="Rows = Cause | Cols = Process" />
            <CardBody style={{ padding: '14px 12px' }}>
              {hm2rows.length === 0
                ? <div style={{ color: SLATE }}>No data available.</div>
                : <Heatmap rows={hm2rows} cols={hm2cols} matrix={hm2} rowLabel="Cause" colLabel="Process" />}
            </CardBody>
          </Card>
        </Section>

        {/* ═══ SECTION 5 — ERROR DISTRIBUTION ═══ */}
        <Section title={ar ? 'توزيع الأخطاء' : 'Error Distribution'} icon="🔍">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16, direction: 'ltr' }}>
            <Card>
              <CardHeader title={ar ? 'الأخطاء حسب مرحلة الدورة' : 'Errors by Medication Error Cycle'} badge={`Total: ${current.total_errors}`} />
              <CardBody style={{ padding: '8px 12px 12px' }}>
                <AdvancedDonut data={cycleData} centerValue={current.total_errors} centerLabel={ar ? 'إجمالي' : 'Total'} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader title={ar ? 'الأخطاء حسب فترة المناوبة' : 'Errors by Duty Shift'} />
              <CardBody style={{ padding: '8px 12px 12px' }}>
                <AdvancedDonut data={shiftData} />
              </CardBody>
            </Card>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, direction: 'ltr' }}>
            <Card>
              <CardHeader title={ar ? 'طريقة اكتشاف الخطأ' : 'Errors by Detection Method'} />
              <CardBody style={{ padding: '10px 0 8px' }}>
                <HBarChart data={detectedData} dataKey="value" nameKey="name" color={GREEN} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader title={ar ? 'الأخطاء حسب الكادر المتسبب' : 'Errors by Staff Involved'} />
              <CardBody style={{ padding: '10px 0 8px' }}>
                <HBarChart data={staffData} dataKey="value" nameKey="name" color="#8b5cf6" />
              </CardBody>
            </Card>
          </div>
        </Section>

        {/* ═══ SECTION 6 — DEPARTMENT ANALYSIS ═══ */}
        <Section title={ar ? 'تحليل الأقسام' : 'Department Analysis'} icon="🏥">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, direction: 'ltr' }}>
            <Card>
              <CardHeader title={ar ? 'أعلى 8 أقسام حسب عدد الأخطاء' : 'Top 8 Departments by Errors'} />
              <CardBody style={{ padding: '10px 0 8px' }}>
                <HBarChart data={deptData.slice(0, 8)} dataKey="count" nameKey="dept" color={BLUE} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader title={ar ? 'جدول تفصيلي — الأقسام' : 'Department Executive Table'} />
              <div style={{ overflowY: 'auto', maxHeight: 480 }}>
                <DeptTable deptData={deptData} totalErrors={totalDeptErrors} ar={ar} />
              </div>
            </Card>
          </div>
        </Section>

        {/* ═══ SECTION 7 — TREND ANALYSIS ═══ */}
        <Section title={ar ? 'تحليل الاتجاهات' : 'Trend Analysis'} icon="📈">

          {/* All quarters area trend */}
          <Card style={{ marginBottom: 16 }}>
            <CardHeader title={ar ? 'تطور عدد الأخطاء — جميع الفصول' : 'Total Errors Trend — All Quarters'} />
            <CardBody style={{ padding: '12px 8px 8px' }}>
              <div dir="ltr">
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={trendData} margin={{ top: 24, right: 16, left: 0, bottom: 44 }}>
                    <defs>
                      <linearGradient id="errGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={BLUE} stopOpacity={0.15} />
                        <stop offset="95%" stopColor={BLUE} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="label" interval={0} angle={-30} textAnchor="end" height={60} tick={{ fontSize: 10, fill: '#64748b' }} />
                    <YAxis hide />
                    <Tooltip {...TS} formatter={v => [`${v} errors`]} />
                    <Area type="monotone" dataKey="errors" name="Total Errors" stroke={BLUE} strokeWidth={2.5}
                      fill="url(#errGrad)" dot={{ r: 5, fill: BLUE }}
                      label={{ position: 'top', fontSize: 11, fontWeight: 700, fill: BLUE }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardBody>
          </Card>

          {/* ALL quarters comparison: bars + rate line */}
          <Card>
            <CardHeader
              title={ar ? 'مقارنة جميع الفصول' : 'All Quarters Comparison — Errors & Rate'}
              badge={`${sorted.length} quarters`}
            />
            <CardBody style={{ padding: '12px 8px 8px' }}>
              <div dir="ltr">
                <ResponsiveContainer width="100%" height={380}>
                  <ComposedChart data={trendData} margin={{ top: 24, right: 50, left: 8, bottom: 50 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="label" interval={0} angle={-30} textAnchor="end" height={60} tick={{ fontSize: 10, fill: '#64748b' }} />
                    <YAxis yAxisId="left" allowDecimals={false} tick={{ fontSize: 11 }} width={36} />
                    <YAxis yAxisId="right" orientation="right" tickFormatter={v => `${v.toFixed(3)}%`} tick={{ fontSize: 11, fill: RED }} width={42} />
                    <Tooltip {...TS} formatter={(v, name) => name === 'Error Rate' ? [`${v.toFixed(4)}%`, name] : [v, name]} />
                    <Legend verticalAlign="top" height={32} />
                    <Bar yAxisId="left" dataKey="errors" name="Total Errors" fill={BLUE} radius={[5, 5, 0, 0]} barSize={40}
                      label={{ position: 'top', fontSize: 10, fontWeight: 700, fill: BLUE }} />
                    <Line yAxisId="right" type="monotone" dataKey="rate" name="Error Rate" stroke={RED} strokeWidth={2.5}
                      dot={{ r: 4, fill: RED }} activeDot={{ r: 7 }}
                      label={{ position: 'top', fontSize: 10, fontWeight: 600, fill: RED, formatter: v => `${v.toFixed(4)}%` }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardBody>
          </Card>
        </Section>

      </div>
    </>
  );
}

export default MedicationDashboard;