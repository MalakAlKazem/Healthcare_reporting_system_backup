import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/Dashboard.module.css';

import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

function Dashboard({ data }) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (data) {
      calculateStatistics(data);
    }
  }, [data]);

  const calculateStatistics = (mortalityData) => {
    // Safety check
    if (!mortalityData || !mortalityData.records || !Array.isArray(mortalityData.records)) {
      console.error('Invalid mortality data structure:', mortalityData);
      return;
    }
    
    const records = mortalityData.records;

    const totalDeaths = records.length;
    const averageAge = records.reduce((sum, r) => sum + (r.age || 0), 0) / totalDeaths;
    const averageLOS = records.reduce((sum, r) => sum + (r.los || 0), 0) / totalDeaths;
    
    const maleDeaths = records.filter(r => r.gender === 'ذكر' || r.gender === 'male').length;
    const femaleDeaths = records.filter(r => r.gender === 'انثى' || r.gender === 'female').length;
    const malePercentage = ((maleDeaths / totalDeaths) * 100).toFixed(1);

    // Monthly data
    const monthlyData = {};
    records.forEach(r => {
      const month = r.month || 'Unknown';
      monthlyData[month] = (monthlyData[month] || 0) + 1;
    });

    const monthlyChart = Object.entries(monthlyData)
      .map(([month, count]) => ({
        month: getMonthName(month, i18n.language),
        deaths: count
      }))
      .sort((a, b) => parseInt(a.month) - parseInt(b.month));

    // Age distribution
    const ageGroups = {
      '0-20': 0,
      '21-40': 0,
      '41-60': 0,
      '61-80': 0,
      '81+': 0
    };

    records.forEach(r => {
      const age = r.age || 0;
      if (age <= 20) ageGroups['0-20']++;
      else if (age <= 40) ageGroups['21-40']++;
      else if (age <= 60) ageGroups['41-60']++;
      else if (age <= 80) ageGroups['61-80']++;
      else ageGroups['81+']++;
    });

    const ageChart = Object.entries(ageGroups).map(([range, count]) => ({
      range,
      count
    }));

    // Top causes
    const causesCount = {};
    records.forEach(r => {
      const cause = r.direct_cause_of_death || 'Unknown';
      causesCount[cause] = (causesCount[cause] || 0) + 1;
    });

    const topCauses = Object.entries(causesCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([cause, count]) => ({ cause, count }));

    setStats({
      totalDeaths,
      averageAge: averageAge.toFixed(1),
      averageLOS: averageLOS.toFixed(1),
      maleDeaths,
      femaleDeaths,
      malePercentage,
      monthlyChart,
      ageChart,
      topCauses
    });
  };

  const getMonthName = (monthNum, lang) => {
    const monthsAr = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 
                      'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
    const monthsEn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const index = parseInt(monthNum) - 1;
    return lang === 'ar' ? monthsAr[index] || monthNum : monthsEn[index] || monthNum;
  };

  if (!data) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📊</div>
        <h2 className={styles.emptyTitle}>{t('noDataYet')}</h2>
        <p className={styles.emptyText}>{t('uploadDataToGetStarted')}</p>
        <button onClick={() => navigate('/upload')} className={styles.uploadButton}>
          <span>📤</span>
          <span>{t('uploadData')}</span>
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>⏳</div>
        <h2 className={styles.emptyTitle}>{t('processing')}</h2>
        <p className={styles.emptyText}>{t('pleaseWait')}</p>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      {/* Page Header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>{t('dashboard')}</h1>
          <p className={styles.pageSubtitle}>{t('overviewOfMortalityData')}</p>
        </div>
        <div className={styles.datebadge}>
          {new Date().toLocaleDateString(i18n.language === 'ar' ? 'ar-SA' : 'en-US', {
            year: 'numeric',
            month: 'long'
          })}
        </div>
      </div>

      {/* KPI Cards - Clean Design */}
      <div className={styles.kpiGrid}>
        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiIcon}>💀</span>
            <span className={styles.kpiLabel}>{t('totalDeaths')}</span>
          </div>
          <div className={styles.kpiValue}>{stats.totalDeaths.toLocaleString()}</div>
          <div className={styles.kpiFooter}>
            <span className={styles.kpiTrend}>Total recorded cases</span>
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiIcon}>👴</span>
            <span className={styles.kpiLabel}>{t('averageAge')}</span>
          </div>
          <div className={styles.kpiValue}>{stats.averageAge}</div>
          <div className={styles.kpiFooter}>
            <span className={styles.kpiTrend}>{t('years')}</span>
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiIcon}>🏥</span>
            <span className={styles.kpiLabel}>{t('averageLOS')}</span>
          </div>
          <div className={styles.kpiValue}>{stats.averageLOS}</div>
          <div className={styles.kpiFooter}>
            <span className={styles.kpiTrend}>{t('days')}</span>
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiIcon}>👥</span>
            <span className={styles.kpiLabel}>{t('male')} / {t('female')}</span>
          </div>
          <div className={styles.kpiValue}>{stats.malePercentage}%</div>
          <div className={styles.kpiFooter}>
            <span className={styles.kpiTrend}>
              ♂️ {stats.maleDeaths} / ♀️ {stats.femaleDeaths}
            </span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className={styles.chartsGrid}>
        {/* Monthly Trend */}
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}>
            <h3 className={styles.chartTitle}>{t('monthlyTrend')}</h3>
          </div>
          <div className={styles.chartBody}>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={stats.monthlyChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="month" 
                  stroke="#64748b" 
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                  }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="deaths" 
                  stroke="#3b82f6" 
                  strokeWidth={2.5}
                  name={t('deaths')}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Age Distribution */}
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}>
            <h3 className={styles.chartTitle}>{t('ageDistribution')}</h3>
          </div>
          <div className={styles.chartBody}>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={stats.ageChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="range" 
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                  }}
                />
                <Bar 
                  dataKey="count" 
                  fill="#10b981" 
                  name={t('deaths')}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Causes - Clean Table */}
      <div className={styles.tableCard}>
        <div className={styles.tableHeader}>
          <h3 className={styles.tableTitle}>{t('topCausesOfDeath')}</h3>
        </div>
        <div className={styles.tableBody}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>#</th>
                <th className={styles.th}>{t('causesOfDeath')}</th>
                <th className={styles.th}>{t('deaths')}</th>
                <th className={styles.th}>%</th>
              </tr>
            </thead>
            <tbody>
              {stats.topCauses.map((cause, index) => (
                <tr key={index} className={styles.tr}>
                  <td className={styles.td}>
                    <span className={styles.rank}>{index + 1}</span>
                  </td>
                  <td className={styles.td}>{cause.cause}</td>
                  <td className={styles.td}>
                    <span className={styles.count}>{cause.count}</span>
                  </td>
                  <td className={styles.td}>
                    {((cause.count / stats.totalDeaths) * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;