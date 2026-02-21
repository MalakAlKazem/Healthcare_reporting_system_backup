import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import styles from '../styles/Analysis.module.css';

import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter
} from 'recharts';

function Analysis({ data }) {
  const { t } = useTranslation();
  const [analysisType, setAnalysisType] = useState('trend');
  const [selectedMetric, setSelectedMetric] = useState('age');
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    if (data) {
      generateInsights(data);
    }
  }, [data, analysisType]);

  const generateInsights = (mortalityData) => {
    const records = mortalityData.records;
    const newInsights = [];

    // Age-related insights
    const avgAge = records.reduce((sum, r) => sum + (r.age || 0), 0) / records.length;
    newInsights.push({
      title: t('avgAge'),
      value: avgAge.toFixed(1),
      description: t('yearsOld')
    });

    // Length of Stay insights
    const avgLOS = records.reduce((sum, r) => sum + (r.los || 0), 0) / records.length;
    newInsights.push({
      title: t('avgLOS'),
      value: avgLOS.toFixed(1),
      description: t('days')
    });

    // High-risk age groups
    const elderlyDeaths = records.filter(r => r.age >= 65).length;
    const elderlyPercentage = (elderlyDeaths / records.length * 100).toFixed(1);
    newInsights.push({
      title: t('elderlyDeaths'),
      value: `${elderlyPercentage}%`,
      description: t('ageAbove65')
    });

    setInsights(newInsights);
  };

  const getTrendData = () => {
    if (!data) return [];
    
    const records = data.records;
    const monthlyData = {};
    
    records.forEach(r => {
      const month = r.month || 'Unknown';
      if (!monthlyData[month]) {
        monthlyData[month] = { month, deaths: 0, totalAge: 0, totalLOS: 0, count: 0 };
      }
      monthlyData[month].deaths += 1;
      monthlyData[month].totalAge += r.age || 0;
      monthlyData[month].totalLOS += r.los || 0;
      monthlyData[month].count += 1;
    });

    return Object.values(monthlyData).map(m => ({
      month: m.month,
      deaths: m.deaths,
      avgAge: (m.totalAge / m.count).toFixed(1),
      avgLOS: (m.totalLOS / m.count).toFixed(1)
    }));
  };

  const getCorrelationData = () => {
    if (!data) return [];
    
    return data.records.map((r, index) => ({
      age: r.age || 0,
      los: r.los || 0,
      name: `Patient ${index + 1}`
    }));
  };

  if (!data) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyStateBackground}></div>
        <div className={styles.emptyStateContent}>
          <div className={styles.emptyStateIconWrapper}>
            <span className={styles.emptyStateIcon}>📈</span>
          </div>
          <h2 className={styles.emptyStateTitle}>
            {t('noDataForAnalysis')}
          </h2>
          <p className={styles.emptyStateText}>
            {t('uploadDataFirst')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.analysisContainer}>
      {/* Header with Gradient */}
      <div className={styles.analysisHeader}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <div className={styles.headerIconWrapper}>
              <div className={styles.headerIcon}>🔬</div>
              <h1 className={styles.headerTitle}>
                {t('dataAnalysis')}
              </h1>
            </div>
            <p className={styles.headerSubtitle}>
              {t('advancedAnalytics')}
            </p>
          </div>
          <div className={styles.headerDecoration}>🧪</div>
        </div>
      </div>

      {/* Analysis Type Selector */}
      <div className={styles.typeSelector}>
        <div className={styles.typeSelectorGrid}>
          <button
            onClick={() => setAnalysisType('trend')}
            className={`${styles.typeButton} ${
              analysisType === 'trend'
                ? `${styles.typeButtonActive} ${styles.trendButton}`
                : styles.typeButtonInactive
            }`}
          >
            <span className={styles.typeButtonIcon}>📈</span>
            {t('trendAnalysis')}
          </button>
          <button
            onClick={() => setAnalysisType('correlation')}
            className={`${styles.typeButton} ${
              analysisType === 'correlation'
                ? `${styles.typeButtonActive} ${styles.correlationButton}`
                : styles.typeButtonInactive
            }`}
          >
            <span className={styles.typeButtonIcon}>🥧</span>
            {t('correlationAnalysis')}
          </button>
        </div>
      </div>

      {/* Key Insights */}
      <div className={styles.insightsGrid}>
        {insights.map((insight, index) => (
          <div key={index} className={styles.insightCard}>
            <div className={styles.insightContent}>
              <div className={styles.insightIconWrapper}>
                <span className={styles.insightIcon}>{index === 0 ? '👴' : index === 1 ? '🏥' : '⚠️'}</span>
              </div>
              <h3 className={styles.insightTitle}>
                {insight.title}
              </h3>
              <div className={styles.insightValue}>
                {insight.value}
              </div>
              <p className={styles.insightDescription}>
                {insight.description}
              </p>
              <div className={styles.insightProgress}>
                <div className={styles.insightProgressBar}></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Analysis Charts */}
      <div className={`${styles.chartSection} ${analysisType === 'trend' ? styles.trendChart : styles.correlationChart}`}>
        {analysisType === 'trend' && (
          <div>
            <div className={styles.chartHeader}>
              <div className={styles.chartIcon}>📉</div>
              <h2 className={styles.chartTitle}>
                {t('mortalityTrends')}
              </h2>
            </div>
            <div className={styles.chartContainer}>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={getTrendData()}>
                  <defs>
                    <linearGradient id="colorDeathsTrend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorAgeTrend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                  <XAxis dataKey="month" stroke="#6366f1" fontWeight="600" />
                  <YAxis stroke="#6366f1" fontWeight="600" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      borderRadius: '12px', 
                      border: '2px solid #e0e7ff',
                      boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
                    }} 
                  />
                  <Legend wrapperStyle={{ fontWeight: '600' }} />
                  <Line 
                    type="monotone" 
                    dataKey="deaths" 
                    stroke="#6366f1" 
                    strokeWidth={4}
                    name={t('deaths')}
                    dot={{ fill: '#6366f1', r: 6, strokeWidth: 2, stroke: '#fff' }}
                    activeDot={{ r: 10 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="avgAge" 
                    stroke="#10b981" 
                    strokeWidth={4}
                    name={t('avgAge')}
                    dot={{ fill: '#10b981', r: 6, strokeWidth: 2, stroke: '#fff' }}
                    activeDot={{ r: 10 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {analysisType === 'correlation' && (
          <div>
            <div className={styles.chartHeader}>
              <div className={styles.chartIcon}>🔗</div>
              <h2 className={styles.chartTitle}>
                {t('ageVsLOS')}
              </h2>
            </div>
            <div className={styles.chartContainer}>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="#fecdd3" />
                  <XAxis dataKey="age" name={t('age')} stroke="#e11d48" fontWeight="600" />
                  <YAxis dataKey="los" name={t('lengthOfStay')} stroke="#e11d48" fontWeight="600" />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }} 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      borderRadius: '12px', 
                      border: '2px solid #fecdd3',
                      boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Legend wrapperStyle={{ fontWeight: '600' }} />
                  <Scatter 
                    name={t('patients')} 
                    data={getCorrelationData()} 
                    fill="#ec4899"
                    shape="circle"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* AI Recommendations Section */}
      <div className={styles.recommendations}>
        <div className={styles.recommendationsContent}>
          <div className={styles.recommendationsHeader}>
            <div className={styles.recommendationsIcon}>🤖</div>
            <h2 className={styles.recommendationsTitle}>
              {t('aiRecommendations')}
            </h2>
          </div>
          <div className={styles.recommendationsList}>
            <div className={styles.recommendationsItems}>
              <div className={styles.recommendationItem}>
                <div className={styles.recommendationIcon}>✅</div>
                <span className={styles.recommendationText}>{t('recommendation1')}</span>
              </div>
              <div className={styles.recommendationItem}>
                <div className={styles.recommendationIcon}>✅</div>
                <span className={styles.recommendationText}>{t('recommendation2')}</span>
              </div>
              <div className={styles.recommendationItem}>
                <div className={styles.recommendationIcon}>✅</div>
                <span className={styles.recommendationText}>{t('recommendation3')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Analysis;
