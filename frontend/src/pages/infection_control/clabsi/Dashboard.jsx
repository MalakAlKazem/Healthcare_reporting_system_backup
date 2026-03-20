import React, { useEffect, useState } from "react";
import styles from "../styles/Dashboard.module.css";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";
const API_URL = "http://localhost:8000/api/clabsi";

/* ───────────────────────────────────────────── */
/* COLORS                                        */
/* ───────────────────────────────────────────── */

const GREEN = "#16a34a";
const RED = "#dc2626";
const AMBER = "#f59e0b";
const BORDER = "#e5e7eb";
const SLATE = "#64748b";
const TS = {
  contentStyle: {
    background: "#fff",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
    padding: "10px 14px",
    boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
    fontSize: "12px"
  }
};
const thStyle = {
  padding: "12px 10px",
  textAlign: "left",
  fontWeight: 600,
  color: "#334155",
  borderBottom: "1px solid #e2e8f0"
};

const tdStyle = {
  padding: "10px",
  borderBottom: "1px solid #e2e8f0"
};
/* ───────────────────────────────────────────── */
/* TARGETS (per 1000 catheter days)              */
/* ───────────────────────────────────────────── */

const TARGETS = {
  ICU: 10,
  CCU: 9,
  CSU: 4,
  ICN: 14,
  Pediatric: 8,
  ITU: 10
};

/* ───────────────────────────────────────────── */
/* Executive Semicircle Gauge                    */
/* ───────────────────────────────────────────── */

function DepartmentGauge({ name, rate, target }) {
  const MAX = Math.max(rate * 1.5, target * 2, 5);;
  const ratePct = Math.min(rate, MAX) / MAX;
  const tgtPct = Math.min(target, MAX) / MAX;
  const isAbove = rate > target;

  const arc = (pct, radius) => {
    const angle = Math.PI * pct;
    const x = 100 - radius * Math.cos(angle);
    const y = 100 - radius * Math.sin(angle);

    // Always use small arc (0) for semicircle
    return `M ${100 - radius} 100 
            A ${radius} ${radius} 0 0 1 ${x} ${y}`;
  };
  return (
    <div
      style={{
        background: "white",
        borderRadius: 20,
        padding: 24,
        boxShadow: "0 8px 25px rgba(0,0,0,0.05)",
        textAlign: "center"
      }}
    >
      <h3 style={{ marginBottom: 12 }}>{name}</h3>

      <svg viewBox="0 0 200 115" width="100%" style={{ maxWidth: 280 }}>
        {/* Background */}
        <path
          d={arc(1, 70)}
          fill="none"
          stroke={BORDER}
          strokeWidth="16"
          strokeLinecap="round"
        />

        {/* Value */}
        <path
          d={arc(ratePct, 70)}
          fill="none"
          stroke={isAbove ? RED : GREEN}
          strokeWidth="14"
          strokeLinecap="round"
        />

        {/* Target Marker */}
        <line
          x1={100 - 62 * Math.cos(Math.PI * tgtPct)}
          y1={100 - 62 * Math.sin(Math.PI * tgtPct)}
          x2={100 - 80 * Math.cos(Math.PI * tgtPct)}
          y2={100 - 80 * Math.sin(Math.PI * tgtPct)}
          stroke={AMBER}
          strokeWidth="4"
          strokeLinecap="round"
        />

        {/* Rate */}
        <text
          x="100"
          y="82"
          textAnchor="middle"
          fontSize="22"
          fontWeight="800"
          fill={isAbove ? RED : GREEN}
        >
          {rate.toFixed(2)}‰
        </text>

        <text
          x="100"
          y="98"
          textAnchor="middle"
          fontSize="10"
          fill="#94a3b8"
        >
          target {target}‰
        </text>
      </svg>

      {/* Status */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          background: isAbove ? "#fef2f2" : "#f0fdf4",
          color: isAbove ? RED : GREEN,
          borderRadius: 20,
          padding: "5px 16px",
          fontSize: 12,
          fontWeight: 700,
          marginTop: 6
        }}
      >
        {isAbove ? "▲ Above Target" : "▼ Below Target"}
      </div>

      {/* Bottom metrics */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 16,
          marginTop: 16,
          fontSize: 12,
          color: SLATE
        }}
      >
        {[
          {
            label: "Actual",
            value: `${rate.toFixed(2)}‰`,
            color: isAbove ? RED : GREEN
          },
          {
            label: "Target",
            value: `${target}‰`,
            color: AMBER
          },
          {
            label: isAbove ? "Over" : "Under",
            value: `${Math.abs(rate - target).toFixed(2)}‰`,
            color: isAbove ? RED : GREEN
          }
        ].map((item, i, arr) => (
          <React.Fragment key={item.label}>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  color: item.color
                }}
              >
                {item.value}
              </div>
              <div style={{ marginTop: 2 }}>{item.label}</div>
            </div>
            {i < arr.length - 1 && (
              <div style={{ width: 1, background: BORDER }} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

/* ───────────────────────────────────────────── */
/* Dashboard                                     */
/* ───────────────────────────────────────────── */

function ClabsiDashboard({ language }) {
  const [history, setHistory] = useState([]);
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/history`)
      .then(res => res.json())
      .then(result => {
        if (Array.isArray(result) && result.length > 0) {
          setHistory(result);
          setCurrent(result[result.length - 1]); // latest quarter
        }
        setLoading(false);
      })
      .catch(error => {
        console.error("Dashboard error:", error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className={styles.emptyState}>Loading...</div>;
  }

  if (!current || !current.summary) {
    return (
      <div className={styles.emptyState}>
        <h2>No Data Available</h2>
      </div>
    );
  }

  return (

<div className={styles.dashboard} dir="ltr">
{/* ================= CLABSI Quarterly Performance Summary ================= */}
  <div
    style={{
      background: "#ffffff",
      borderRadius: "14px",
      boxShadow: "0 6px 18px rgba(0,0,0,0.06)",
      overflow: "hidden"
    }}
  >
    {/* Header */}
    <div
      style={{
        padding: "1rem 1.5rem",
        background: "linear-gradient(to right, #dbeafe, #ffffff)",
        borderBottom: "1px solid #e2e8f0"
      }}
    >
      <h3 style={{ margin: 0, color: "#1e3a8a" }}>
        CLABSI Quarterly Performance Summary
      </h3>
    </div>

    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "14px",
          tableLayout: "fixed"
        }}
      >
        {/* Header Row */}
        <thead style={{ background: "#f1f5f9" }}>
          <tr>
            <th style={thStyle}>Department (Target)</th>
            {history.map((q, index) => (
              <th key={index} style={thStyle}>
                Q{q.quarter} {q.year}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {Object.keys(TARGETS).map((dept, rowIndex) => {

            return (
              <tr
                key={dept}
                style={{
                  background:
                    rowIndex % 2 === 0 ? "#ffffff" : "#f8fafc"
                }}
              >
                {/* Department Column */}
  <td
    style={{
      ...tdStyle,
      fontWeight: 600,
      color: "#1e293b",
      minWidth: 50
    }}
  >
  <div style={{ display: "flex", flexDirection: "column" }}>
    <span>{dept}</span>

    <span
      style={{
        fontSize: "12px",
        color: "#64748b",
        marginTop: 2
      }}
    >
      Target: {TARGETS[dept]}‰
    </span>

      <span
        style={{
          fontSize: "12px",
          marginTop: 4,
          fontWeight: 600,
          color:
            history[history.length - 1].summary?.[dept]?.rate >
            TARGETS[dept]
              ? "#dc2626"
              : "#16a34a"
        }}
      >
        Latest: {history[history.length - 1].summary?.[dept]?.rate ?? "—"}‰
      </span>
    </div>
  </td>

                {/* Quarter Cells */}
                {history.map((q, colIndex) => {

                  const summary = q.summary?.[dept];

                  const cases = summary?.cases ?? null;
                  const days = summary?.catheter_days ?? null;
                  const rate = summary?.rate ?? null;

                  const target = TARGETS[dept];

                  const isAboveTarget =
                    rate !== null && rate > target;

                  // Previous quarter rate (for arrow comparison)
                  const prevRate =
                    colIndex > 0
                      ? history[colIndex - 1].summary?.[dept]?.rate ?? null
                      : null;

                  let trendArrow = "";
                  if (prevRate !== null && rate !== null) {
                    if (rate > prevRate) trendArrow = " ↑";
                    if (rate < prevRate) trendArrow = " ↓";
                  }

                  return (
                    <td
                      key={colIndex}
                      style={{
                        ...tdStyle,
                        textAlign: "center",
                        background: isAboveTarget
                          ? "#fee2e2"
                          : "transparent",
                        color: isAboveTarget
                          ? "#b91c1c"
                          : "#0f172a"
                      }}
                    >
                      {rate !== null ? (
                        <>
                          {/* Cases / Catheter Days */}
                          <div style={{ fontSize: 13 }}>
                            <span style={{ fontWeight: 700 }}>
                              {cases}
                            </span>
                            <span style={{ color: "#64748b" }}>
                              {" "}
                              / {days}
                            </span>
                          </div>

                          {/* Rate + Trend */}
                          <div
                            style={{
                              fontSize: 12,
                              fontWeight: 600
                            }}
                          >
                            {rate}‰{trendArrow}
                          </div>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
    {/* ================= DEPARTMENT BLOCKS ================= */}
    <div style={{ marginTop: "3rem" }}>

      {Object.keys(TARGETS).map((dept) => {

        const latestQuarter = history[history.length - 1];
        const latestSummary = latestQuarter.summary?.[dept];

        if (!latestSummary) return null;

        /* ================= TREND DATA ================= */
        const trendData = history.map((q) => ({
          label: `Q${q.quarter} ${q.year}`,
          rate: q.summary?.[dept]?.rate || 0,
          target: TARGETS[dept]
        }));

        /* ================= CASES ================= */
        const deptCases = history
          .flatMap(q => q.cases || [])
          .filter(c => c.Floor === dept);

        const buildRiskFactors = (caseItem) => {
          const riskFields = [
            "Diabetic",
            "Hypertension",
            "Dyslipidemia",
            "Heart disease",
            "kidney disease",
            "COPD",
            "Smoker",
            "Obesity",
            "Cardiac congenital malformation",
            "Advanced age",
            "length of stay",
            "Duration of catheter",
            "cancer",
            "Compromised immune system",
            "Respiratory Pb"
          ];

          return riskFields
            .filter(field => caseItem[field] === "Yes")
            .join(", ");
        };

        return (
          <div
            key={dept}
            style={{
              marginBottom: "4rem",
              background: "#ffffff",
              borderRadius: "16px",
              boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
              padding: "2rem"
            }}
          >

            {/* ===== Department Title ===== */}
<h2 style={{ marginBottom: "2rem", color: "#1e3a8a" }}>
  {dept} Performance in Q{latestQuarter.quarter} {latestQuarter.year}
</h2>
            {/* ===== Gauge + Trend ===== */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "300px 1fr",
                gap: "2rem",
                marginBottom: "2rem"
              }}
            >

              {/* Gauge */}
              <DepartmentGauge
                name={dept}
                rate={latestSummary.rate}
                target={TARGETS[dept]}
              />

              {/* Trend Line */}
              <div
                style={{
                  background: "white",
                  borderRadius: 20,
                  padding: 20,
                  boxShadow: "0 8px 25px rgba(0,0,0,0.05)"
                }}
              >
              <h3 style={{ marginBottom: 16 }}>
                Quarterly CLABSI Rate vs Target
                <span style={{ color: "#dc2626", fontWeight: 600 }}>
                  {" "}({TARGETS[dept]}‰)
                </span>
              </h3>
              <ResponsiveContainer width="100%" height={300}>
  <LineChart
    data={trendData}
    margin={{ top: 30, right: 20, left: 40, bottom: 20 }}  >
    <CartesianGrid
      strokeDasharray="3 3"
      stroke="#f1f5f9"
      vertical={false}
    />

    <XAxis
      dataKey="label"
      interval={0}
      angle={-30}
      textAnchor="end"
      height={60}
      tick={{ fontSize: 10 }}
    />

    <YAxis hide />

    <Tooltip
      {...TS}
      formatter={(value, name) => [
        `${value.toFixed(2)}‰`,
        name === "rate" ? "Actual" : "Target"
      ]}
    />

    <Legend verticalAlign="top" height={30} />

    {/* ===== ACTUAL LINE ===== */}
    <Line
      type="monotone"
      dataKey="rate"
      name="Actual Rate"
      stroke="#2563eb"
      strokeWidth={2.5}
      dot={{ r: 4, fill: "#2563eb" }}
      
      label={{
        position: "top",
        fontSize: 10,
        fontWeight: 700,
        fill: "#2563eb",
        formatter: (v) => `${v.toFixed(1)}‰`
      }}
    />

    {/* ===== TARGET LINE ===== */}
    <Line
      type="monotone"
      dataKey="target"
      name="Target"
      stroke="#dc2626"
      strokeDasharray="6 3"
      strokeWidth={2}
      dot={false}
    />
  </LineChart>
</ResponsiveContainer>
              </div>
            </div>

            {/* ===== HEATMAP (REUSE YOUR EXISTING HEATMAP BLOCK HERE) ===== */}
            {/* ===== Germ Heatmap ===== */}

  {(() => {

  const normalize = (germ) => germ?.toLowerCase().trim();

  const validQuarters = history.filter(q => {
    const hasDistribution =
      q.germs_distribution &&
      q.germs_distribution[dept] &&
      Object.keys(q.germs_distribution[dept]).length > 0;

    const hasCases =
      q.cases &&
      q.cases.some(c => c.Floor === dept);

    return hasDistribution || hasCases;
  });

  if (!validQuarters.length) return null;

  const quarterKeys = validQuarters.map(
    q => `Q${q.quarter} ${q.year}`
  );

  const latestQuarterKey =
    quarterKeys[quarterKeys.length - 1];

  const germMap = new Map();

  validQuarters.forEach(q => {

    if (q.germs_distribution && q.germs_distribution[dept]) {
      Object.keys(q.germs_distribution[dept]).forEach(g => {
        const key = normalize(g);
        if (!germMap.has(key)) germMap.set(key, g);
      });
    }

    if (q.cases) {
      q.cases
        .filter(c => c.Floor === dept)
        .forEach(c => {
          const key = normalize(c.Germs);
          if (!germMap.has(key)) germMap.set(key, c.Germs);
        });
    }
  });

  const germs = Array.from(germMap.keys());

  const data = germs.map(germKey => {

    const row = { germ: germMap.get(germKey), values: {} };

    validQuarters.forEach(q => {

      const qKey = `Q${q.quarter} ${q.year}`;
      let germCount = 0;
      const totalCases = q.summary?.[dept]?.cases || 0;

      if (q.germs_distribution && q.germs_distribution[dept]) {
        Object.entries(q.germs_distribution[dept]).forEach(([g, count]) => {
          if (normalize(g) === germKey) {
            germCount += count;
          }
        });
      }

      if (q.cases) {
        germCount += q.cases
          .filter(c =>
            c.Floor === dept &&
            normalize(c.Germs) === germKey
          )
          .reduce(
            (sum, c) => sum + Number(c["Nb of cases"] || 0),
            0
          );
      }

      const percent =
        totalCases > 0
          ? (germCount / totalCases) * 100
          : 0;

      row.values[qKey] = {
        count: germCount,
        percent
      };
    });

    return row;
  });

  data.sort((a, b) =>
    b.values[latestQuarterKey].percent -
    a.values[latestQuarterKey].percent
  );

  const TOP_N = 6;
  const filteredData = data.slice(0, TOP_N);

  const maxPercent = Math.max(
    ...filteredData.flatMap(row =>
      quarterKeys.map(q => row.values[q].percent)
    ),
    1
  );

  const getColor = (percent, qKey) => {

    const normalized = percent / maxPercent;

    const start = { r: 219, g: 234, b: 254 };
    const end   = { r: 30,  g: 64,  b: 175 };

    let r = Math.round(start.r + (end.r - start.r) * normalized);
    let g = Math.round(start.g + (end.g - start.g) * normalized);
    let b = Math.round(start.b + (end.b - start.b) * normalized);

    if (qKey === latestQuarterKey) {
      r = Math.max(r - 15, 0);
      g = Math.max(g - 15, 0);
      b = Math.max(b - 15, 0);
    }

    return `rgb(${r}, ${g}, ${b})`;
  };

  return (
    <div style={{ marginBottom: "2rem" }}>
      <h3 style={{ marginBottom: 16 }}>
        Germ Distribution Heatmap
      </h3>

      <div style={{ overflowX: "auto" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `200px repeat(${quarterKeys.length}, 1fr)`,
            gap: 6
          }}
        >
          <div></div>
          {quarterKeys.map(q => (
            <div key={q} style={{ textAlign: "center", fontSize: 12 }}>
              {q}
            </div>
          ))}

          {filteredData.map(row => (
            <React.Fragment key={row.germ}>
              <div style={{ fontSize: 12 }}>
                {row.germ}
              </div>

              {quarterKeys.map(q => {
                const cell = row.values[q];
                return (
                  <div
                    key={q}
                    style={{
                      background: getColor(cell.percent, q),
                      borderRadius: 8,
                      padding: 8,
                      textAlign: "center",
                      fontSize: 11,
                      fontWeight: 600,
                      color: cell.percent > 25 ? "#fff" : "#1e293b"
                    }}
                  >
                    {cell.count}
                    <div style={{ fontSize: 10 }}>
                      ({cell.percent.toFixed(0)}%)
                    </div>
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );

})()}


            {/* For simplicity: keep your current heatmap logic but wrap it inside this dept block */}

            {/* ===== DETAILED TABLE ===== */}
            {deptCases.length > 0 && (
              <div
                style={{
                  marginTop: "2rem",
                  background: "#ffffff",
                  borderRadius: "12px",
                  boxShadow: "0 4px 14px rgba(0,0,0,0.06)",
                  overflow: "hidden"
                }}
              >
                <div
                  style={{
                    padding: "1rem 1.5rem",
                    background: "linear-gradient(to right, #e0f2fe, #ffffff)",
                    borderBottom: "1px solid #e2e8f0"
                  }}
                >
                  <h3 style={{ margin: 0 }}>
                    Detailed Cases
                  </h3>
                </div>

                <div style={{ overflowX: "auto" }}>
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: "13px"
                    }}
                  >
                    <thead style={{ background: "#f1f5f9" }}>
                      <tr>
                        <th style={thStyle}>Cases</th>
                        <th style={thStyle}>Diagnosis</th>
                        <th style={thStyle}>Admission</th>
                        <th style={thStyle}>Insertion</th>
                        <th style={thStyle}>Infection</th>
                        <th style={thStyle}>Germ</th>
                        <th style={thStyle}>Line</th>
                        <th style={thStyle}>Age</th>
                        <th style={thStyle}>Risk Factors</th>
                      </tr>
                    </thead>

                    <tbody>
                      {deptCases.map((c, index) => (
                        <tr
                          key={index}
                          style={{
                            background:
                              index % 2 === 0
                                ? "#ffffff"
                                : "#f8fafc"
                          }}
                        >
                          <td style={{ ...tdStyle, fontWeight: 600 }}>
                            {Number(c["Nb of cases"] || 1)}
                          </td>
                          <td style={tdStyle}>{c.Diagnosis}</td>
                          <td style={tdStyle}>{c["Date of admission"]}</td>
                          <td style={tdStyle}>{c["Date of insertion Central line"]}</td>
                          <td style={tdStyle}>{c["Date of infection"]}</td>
                          <td style={{ ...tdStyle, fontWeight: 600 }}>
                            {c.Germs}
                          </td>
                          <td style={tdStyle}>{c["Type of line"]}</td>
                          <td style={tdStyle}>{c["Age/Year"]}</td>
                          <td style={tdStyle}>
                            {buildRiskFactors(c) || "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

          </div>
        );
      })}

    </div>
  </div>

    
    
  );
}

export default ClabsiDashboard;