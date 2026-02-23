// ═══════════════════════════════════════════════════════════════════════════════
// HISTORICAL COMPARISONS — ALL OPTIONS
// Drop this entire block into Dashboard.jsx replacing the existing ROW F section.
//
// SETUP: Add this near the top of Dashboard.jsx alongside other imports:
//   import { ScatterChart, Scatter, ZAxis } from 'recharts';
//
// SETUP: Add this computed value inside the Dashboard function, alongside
//        the existing prevQuarter / lastYearQuarter derivations:
//
//   // All quarters in the current year (excluding the current one if already saved)
//   const yearQuarters = historyData
//     .filter(h => h.year === year)
//     .sort((a, b) => quarterSortKey(a) - quarterSortKey(b));
//
//   // All quarters this year + current quarter combined (for charts)
//   const allThisYear = [
//     ...yearQuarters.filter(h => !(h.quarter === quarter && h.year === year)),
//     // current quarter appended so it's always last (most recent)
//   ];
//   // Short label helper
//   const qShort = (h) => {
//     const map = {
//       'الفصل الاول': 'Q1', 'الفصل الأول': 'Q1',
//       'الفصل الثاني': 'Q2', 'الفصل الثالث': 'Q3', 'الفصل الرابع': 'Q4',
//     };
//     return `${map[h.quarter] || h.quarter} ${h.year}`;
//   };
//   const currentQShort = (() => {
//     const map = {
//       'الفصل الاول': 'Q1', 'الفصل الأول': 'Q1',
//       'الفصل الثاني': 'Q2', 'الفصل الثالث': 'Q3', 'الفصل الرابع': 'Q4',
//     };
//     return `${map[quarter] || quarter} ${year}`;
//   })();
//
// ═══════════════════════════════════════════════════════════════════════════════

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";

const AGE_SHORT = ['<5','5-15','16-30','31-50','51-60','61-70','71-80','81+'];

const COLORS = {
  current: "#1d4ed8",
  grey1: "#cbd5e1",
  grey2: "#94a3b8",
  grey3: "#64748b"
};

export function HistoricalComparisonsSection({
  allThisYear,
  currentQShort,
  stats,
  styles
}) {
  if (!allThisYear || allThisYear.length === 0) return null;

  const year = allThisYear[0]?.year;

  // QUARTER SETUP (GLOBAL — used everywhere)
  const quarterSet = [
    ...allThisYear.map((h, i) => ({
      label: `${h.quarter} ${h.year}`,
      ages: h.age_groups || [],
      depts: h.departments || {},
      color: [COLORS.grey1, COLORS.grey2, COLORS.grey3][i] || COLORS.grey2,
      isCurrent: false
    })),
    {
      label: currentQShort,
      ages: stats.ageArray,
      depts: stats.deptCount,
      color: COLORS.current,
      isCurrent: true
    }
  ];

  // AGE DATA
  const ageData = AGE_SHORT.map((age, i) => {
    const row = { age };
    quarterSet.forEach(q => {
      row[q.label] = q.ages[i] ?? 0;
    });
    return row;
  });

  const ageMax = Math.max(...quarterSet.flatMap(q => q.ages), 1);

  // DEPARTMENT DATA
  const allDepts = Array.from(
    new Set([
      ...Object.keys(stats.deptCount || {}),
      ...allThisYear.flatMap(h => Object.keys(h.departments || {}))
    ])
  );

  const deptMax = Math.max(
    ...quarterSet.flatMap(q => Object.values(q.depts)),
    1
  );

  const sortedDepts = [...allDepts].sort(
    (a, b) =>
      (stats.deptCount?.[b] || 0) -
      (stats.deptCount?.[a] || 0)
  );

  const deptData = sortedDepts.map(dept => {
    const row = { dept };
    quarterSet.forEach(q => {
      row[q.label] = q.depts[dept] ?? 0;
    });
    return row;
  });

  return (
    <>
      {/* SECTION HEADER */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        margin: "40px 0 30px"
      }}>
        <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
        <span style={{ fontSize: 15, fontWeight: 700 }}>
          📊 Year-to-Date Comparison — {year}
        </span>
        <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
      </div>

      {/* AGE SECTION */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 30, marginBottom: 20 }}>

        {/* Clustered Age Chart */}
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}>
            <h3 className={styles.chartTitle}>
              Age Distribution — Quarter Progression
            </h3>
          </div>

          <div className={styles.chartBody}>
            <ResponsiveContainer width="100%" height={420}>
              <BarChart data={ageData} barCategoryGap="25%" barGap={4} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="#eef2f7" vertical={false} />
                <XAxis dataKey="age" tick={{ fontSize: 12 }} />
                <YAxis hide />
                
                <Tooltip />
                <Legend
                    verticalAlign="top"
                    align="center"
                    height={60}
                    wrapperStyle={{
                        fontSize: 12,
                        paddingBottom: 10
                    }}
                    />
                {quarterSet.map(q => (
                  <Bar
                    key={q.label}
                    dataKey={q.label}
                    fill={q.color}
                    radius={[4,4,0,0]}
                    barSize={32}
                    label={
                      q.isCurrent
                        ? {
                            position: "top",
                            formatter: (value, entry, index) => {
                              const prev =
                                quarterSet[quarterSet.length - 2]?.ages[index] ?? 0;
                              if (!prev) return value;
                              const change = ((value - prev) / prev) * 100;
                              const sign = change > 0 ? "+" : "";
                              return `${value} (${sign}${change.toFixed(0)}%)`;
                            },
                            fontSize: 11,
                            fill: "#1e293b"
                          }
                        : false
                    }
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Age Heatmap */}
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}>
            <h3 className={styles.chartTitle}>Age Heatmap</h3>
          </div>

          <div style={{ padding: 20, overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13}}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <th style={{ padding: 10 }}>Age</th>
                  {quarterSet.map(q => (
                    <th
                      key={q.label}
                      style={{
                        padding: 10,
                        fontWeight: q.isCurrent ? 700 : 500,
                        color: q.isCurrent ? COLORS.current : "#475569",
                        borderBottom: "2px solid #e2e8f0"
                      }}
                    >
                      {q.label}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {AGE_SHORT.map((age, i) => (
                  <tr key={age}>
                    <td style={{ padding: 10, fontWeight: 600 }}>{age}</td>
                    {quarterSet.map(q => {
                      const value = q.ages[i] ?? 0;
                      const intensity = value / ageMax;
                      const alpha = (intensity * 0.85 + 0.1).toFixed(2);

                      return (
                        <td
                          key={q.label}
                          style={{
                            padding: 10,
                            textAlign: "center",
                            background: `rgba(31,77,215,${alpha})`,
                            fontWeight: q.isCurrent ? 700 : 500,
                            borderLeft: q.isCurrent
                              ? "3px solid #1f4dd7"
                              : "1px solid #e2e8f0",
                            borderRight: "1px solid #e2e8f0",
                            borderBottom: "1px solid #e2e8f0"
                          }}
                        >
                          {value}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
{/* ── DEPARTMENT SECTION — Executive Polished Version ── */}
<div className={styles.chartCard} style={{ marginTop: 30 }}>

  <div className={styles.chartHeader}>
    <h3 className={styles.chartTitle}>
      Department Performance — Quarter Comparison
    </h3>
  </div>

  <div style={{ padding: "0 20px 24px", overflowX: "auto" }}>

    {(() => {

      const quarterColors = [
        "#cbd5e1", // Q1
        "#94a3b8", // Q2
        "#64748b", // Q3
      ];

      const quarters = quarterSet.map((q, i) => ({
        ...q,
        color: q.isCurrent
          ? "#1f4dd7"
          : quarterColors[i] || "#94a3b8"
      }));

      return (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 13,
            tableLayout: "fixed"
          }}
        >
            <colgroup>
            <col style={{ width: "15%" }} />   {/* Department */}
            <col style={{ width: "20%" }} />   {/* Q1 */}
            <col style={{ width: "20%" }} />   {/* Q2 */}
            <col style={{ width: "25%" }} />   {/* Q3 */}
            <col style={{ width: "20%" }} />   {/* Delta */}
            </colgroup>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              <th
                style={{
                  padding: "14px 10px",
                  textAlign: "left",
                  fontSize: 12,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  color: "#64748b",
                }}
              >
                Department
              </th>

              {quarters.map((q) => (
                <th
                  key={q.label}
                  style={{
                    padding: "14px 10px",
                    textAlign: "center",
                    fontSize: 12,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    fontWeight: q.isCurrent ? 700 : 500,
                    color: q.isCurrent ? "#1f4dd7" : "#64748b",
                    borderBottom: "2px solid #e2e8f0",
                  }}
                >
                  {q.label}
                </th>
              ))}

              <th
                style={{
                  padding: "14px 10px",
                  textAlign: "center",
                  fontSize: 12,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  color: "#64748b",
                  borderLeft: "2px solid #e2e8f0",
                }}
              >
                Δ vs Prev
              </th>
            </tr>
          </thead>

          <tbody>
            {sortedDepts.map((dept) => {
              const current =
                quarters[quarters.length - 1].depts?.[dept] ?? 0;

              const prev =
                quarters.length > 1
                  ? quarters[quarters.length - 2].depts?.[dept] ?? 0
                  : 0;

              const change =
                prev > 0
                  ? ((current - prev) / prev) * 100
                  : null;

              return (
                <tr
                  key={dept}
                  style={{
                    borderBottom: "1px solid #eef2f7",
                  }}
                >
                  {/* Department */}
                  <td
                    style={{
                      padding: "14px 10px",
                      fontWeight: 600,
                      lineHeight: 1.6,
                    }}
                  >
                    {dept}
                  </td>

{/* Quarter Cells */}
{quarters.map((q) => {
  const value = q.depts?.[dept] ?? 0;
  const width =
    deptMax > 0
      ? (value / deptMax) * 100
      : 0;

  return (
    <td
      key={q.label}
      style={{
        padding: "14px 10px",
        backgroundColor: q.isCurrent ? "#f5f8ff" : "transparent",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        {/* Track */}
        <div
          style={{
            flex: 1,
            height: q.isCurrent ? 10 : 8,
            background: "#edf2f7",
            borderRadius: 999,
            overflow: "hidden",
          }}
        >
          {/* Fill */}
          <div
            style={{
              width: `${width}%`,
              height: "100%",
              background: q.color,
              borderRadius: 999,
              transition: "width 0.4s ease",
            }}
          />
        </div>

        {/* Value outside bar */}
        <span
          style={{
            minWidth: 26,
            textAlign: "right",
            fontWeight: q.isCurrent ? 700 : 600,
            color: "#1e293b",
          }}
        >
          {value}
        </span>
      </div>
    </td>
  );
})}
                  {/* Delta Badge */}
                  <td
                    style={{
                      padding: "14px 10px",
                      textAlign: "center",
                      borderLeft: "2px solid #eef2f7",
                    }}
                  >
                    {change === null ? (
                      <span style={{ color: "#94a3b8" }}>—</span>
                    ) : (
                      <span
                        style={{
                          padding: "4px 10px",
                          borderRadius: 20,
                          fontSize: 12,
                          fontWeight: 600,
                          background:
                            change > 0
                              ? "rgba(220,38,38,0.08)"
                              : "rgba(22,163,74,0.08)",
                          color:
                            change > 0
                              ? "#dc2626"
                              : "#16a34a",
                        }}
                      >
                        {change > 0 ? "+" : ""}
                        {change.toFixed(0)}%
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      );
    })()}
  </div>
</div>

    </>
  );
}