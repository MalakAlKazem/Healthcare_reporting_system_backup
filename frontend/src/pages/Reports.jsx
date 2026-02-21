import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import styles from '../styles/Reports.module.css';

function Reports({ data }) {
  const { t } = useTranslation();
  const [reportType, setReportType] = useState('summary');
  const [generating, setGenerating] = useState(false);
  const [reportUrl, setReportUrl] = useState(null);

  // Helper function to translate gender
  const translateGender = (gender) => {
    if (gender === 'ذكر' || gender === 'male') {
      return t('male');
    } else if (gender === 'انثى' || gender === 'female') {
      return t('female');
    }
    return gender;
  };

  const generateSummaryReport = () => {
    if (!data) return null;

    const records = data.records;
    const totalDeaths = records.length;
    const avgAge = (records.reduce((sum, r) => sum + (r.age || 0), 0) / totalDeaths).toFixed(1);
    const maleCount = records.filter(r => r.gender === 'ذكر' || r.gender === 'male').length;
    const femaleCount = records.filter(r => r.gender === 'انثى' || r.gender === 'female').length;

    return {
      totalDeaths,
      avgAge,
      maleCount,
      femaleCount,
      malePercentage: ((maleCount / totalDeaths) * 100).toFixed(1),
      femalePercentage: ((femaleCount / totalDeaths) * 100).toFixed(1)
    };
  };

  const handleGenerateReport = async () => {
    if (!data) {
      alert('Please upload data first');
      return;
    }

    setGenerating(true);

    try {
      const response = await axios.post('http://localhost:8000/api/generate-report', {
        data: data,
        quarter: data.quarter || 'الفصل الثالث',
        year: data.year || '2025',
        language: 'ar'
      });

      if (response.data.success) {
        const downloadUrl = `http://localhost:8000/api/download-report?fileName=${encodeURIComponent(response.data.fileName)}`;
        setReportUrl(downloadUrl);
        alert('Report generated successfully!');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Error generating report');
    } finally {
      setGenerating(false);
    }
  };

  if (!data) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyStateBackground}></div>
        <div className={styles.emptyStateContent}>
          <div className={styles.emptyStateIconWrapper}>
            <span className={styles.emptyStateIcon}>📄</span>
          </div>
          <h2 className={styles.emptyStateTitle}>
            {t('noReportsAvailable')}
          </h2>
          <p className={styles.emptyStateText}>
            {t('uploadDataToGenerateReports')}
          </p>
        </div>
      </div>
    );
  }

  const summaryReport = generateSummaryReport();

  return (
    <div className={styles.reportsContainer}>
      {/* Header with Gradient and Download Button */}
      <div className={styles.reportsHeader}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <div className={styles.headerIconWrapper}>
              <span className={styles.headerIcon}>📊</span>
            </div>
            <div>
              <h1 className={styles.headerTitle}>
                {t('reports')}
              </h1>
              <p className={styles.headerSubtitle}>
                {t('generateAndDownloadReports')}
              </p>
            </div>
          </div>
          <button
            onClick={handleGenerateReport}
            className={styles.downloadButton}
            disabled={generating}
            style={{ opacity: generating ? 0.7 : 1 }}
          >
            <span className={styles.downloadButtonIcon}>📄</span>
            {generating ? t('generating') || 'Generating...' : t('generateWordReport') || 'Generate Word Report'}
          </button>
        </div>
      </div>

      {/* Download Link for Word Report */}
      {reportUrl && (
        <div style={{
          backgroundColor: '#10b981',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem' }}>✅</span>
            <span style={{ fontWeight: 600 }}>
              {t('reportGenerated') || 'Word Report Generated Successfully!'}
            </span>
          </div>
          <a
            href={reportUrl}
            download
            style={{
              backgroundColor: 'white',
              color: '#10b981',
              padding: '0.5rem 1.5rem',
              borderRadius: '8px',
              fontWeight: 'bold',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <span>⬇️</span>
            {t('downloadWord') || 'Download Word Document'}
          </a>
        </div>
      )}

      {/* Report Type Selector with Beautiful Design */}
      <div className={styles.typeSelector}>
        <div className={styles.typeSelectorButtons}>
          <button
            onClick={() => setReportType('summary')}
            className={`${styles.typeButton} ${styles.typeButtonSummary} ${
              reportType === 'summary' ? styles.typeButtonActive : styles.typeButtonInactive
            }`}
          >
            <span className={styles.typeButtonIcon}>📄</span>
            {t('summaryReport')}
          </button>
          <button
            onClick={() => setReportType('detailed')}
            className={`${styles.typeButton} ${styles.typeButtonDetailed} ${
              reportType === 'detailed' ? styles.typeButtonActive : styles.typeButtonInactive
            }`}
          >
            <span className={styles.typeButtonIcon}>📋</span>
            {t('detailedReport')}
          </button>
        </div>
      </div>

      {/* Report Content */}
      {reportType === 'summary' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon}>📊</div>
            <h2 className={styles.reportCardTitle}>
              {t('summaryReport')}
            </h2>
          </div>

          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <div className={styles.statCardContent}>
                <div className={styles.statCardHeader}>
                  <div className={styles.statCardIconWrapper}>
                    <span className={styles.statCardIcon}>💀</span>
                  </div>
                  <h3 className={styles.statCardLabel}>
                    {t('totalDeaths')}
                  </h3>
                </div>
                <div className={styles.statCardValue}>
                  {summaryReport.totalDeaths}
                </div>
                <div className={styles.statCardProgress}>
                  <div className={styles.statCardProgressBar} style={{ width: '100%' }}></div>
                </div>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statCardContent}>
                <div className={styles.statCardHeader}>
                  <div className={styles.statCardIconWrapper}>
                    <span className={styles.statCardIcon}>👴</span>
                  </div>
                  <h3 className={styles.statCardLabel}>
                    {t('averageAge')}
                  </h3>
                </div>
                <div className={styles.statCardValue}>
                  {summaryReport.avgAge}
                  <span className={styles.statCardSubValue}>{t('years')}</span>
                </div>
                <div className={styles.statCardProgress}>
                  <div className={styles.statCardProgressBar} style={{ width: '75%' }}></div>
                </div>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statCardContent}>
                <div className={styles.statCardHeader}>
                  <div className={styles.statCardIconWrapper}>
                    <span className={styles.statCardIcon}>♂️</span>
                  </div>
                  <h3 className={styles.statCardLabel}>
                    {t('maleDeaths')}
                  </h3>
                </div>
                <div className={styles.statCardValue}>
                  {summaryReport.maleCount}
                  <span className={styles.statCardSubValue}>
                    ({summaryReport.malePercentage}%)
                  </span>
                </div>
                <div className={styles.statCardProgress}>
                  <div className={styles.statCardProgressBar} style={{ width: `${summaryReport.malePercentage}%` }}></div>
                </div>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statCardContent}>
                <div className={styles.statCardHeader}>
                  <div className={styles.statCardIconWrapper}>
                    <span className={styles.statCardIcon}>♀️</span>
                  </div>
                  <h3 className={styles.statCardLabel}>
                    {t('femaleDeaths')}
                  </h3>
                </div>
                <div className={styles.statCardValue}>
                  {summaryReport.femaleCount}
                  <span className={styles.statCardSubValue}>
                    ({summaryReport.femalePercentage}%)
                  </span>
                </div>
                <div className={styles.statCardProgress}>
                  <div className={styles.statCardProgressBar} style={{ width: `${summaryReport.femalePercentage}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          <div className={styles.summarySection}>
            <div className={styles.summarySectionHeader}>
              <div className={styles.summarySectionIcon}>
                <span className={styles.summarySectionIconText}>📊</span>
              </div>
              <h3 className={styles.summarySectionTitle}>
                {t('reportSummary')}
              </h3>
            </div>
            <p className={styles.summarySectionText}>
              {t('reportDescription', {
                total: summaryReport.totalDeaths,
                avgAge: summaryReport.avgAge
              })}
            </p>
          </div>
        </div>
      )}

      {reportType === 'detailed' && (
        <div className={styles.reportCard}>
          <div className={styles.reportCardHeader}>
            <div className={styles.reportCardIcon}>📋</div>
            <h2 className={styles.reportCardTitle}>
              {t('detailedReport')}
            </h2>
          </div>

          <div className={styles.tableWrapper}>
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead className={styles.tableHead}>
                  <tr className={styles.tableHeadRow}>
                    <th className={styles.tableHeadCell}>
                      <div className={styles.tableHeadCellContent}>
                        <span className={styles.tableHeadCellIcon}>🔢</span>
                        {t('recordNumber')}
                      </div>
                    </th>
                    <th className={styles.tableHeadCell}>
                      <div className={styles.tableHeadCellContent}>
                        <span className={styles.tableHeadCellIcon}>👴</span>
                        {t('age')}
                      </div>
                    </th>
                    <th className={styles.tableHeadCell}>
                      <div className={styles.tableHeadCellContent}>
                        <span className={styles.tableHeadCellIcon}>👥</span>
                        {t('gender')}
                      </div>
                    </th>
                    <th className={styles.tableHeadCell}>
                      <div className={styles.tableHeadCellContent}>
                        <span className={styles.tableHeadCellIcon}>🏥</span>
                        {t('lengthOfStay')}
                      </div>
                    </th>
                    <th className={styles.tableHeadCell}>
                      <div className={styles.tableHeadCellContent}>
                        <span className={styles.tableHeadCellIcon}>📅</span>
                        {t('month')}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className={styles.tableBody}>
                  {data.records.slice(0, 50).map((record, index) => (
                    <tr key={index} className={styles.tableBodyRow}>
                      <td className={styles.tableBodyCell}>
                        <div className={styles.tableCellNumber}>
                          <div className={styles.tableCellNumberBadge}>
                            {index + 1}
                          </div>
                        </div>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={styles.tableCellAge}>{record.age}</span>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={`${styles.tableCellGenderBadge} ${
                          record.gender === 'ذكر' || record.gender === 'male'
                            ? styles.tableCellGenderMale
                            : styles.tableCellGenderFemale
                        }`}>
                          {record.gender === 'ذكر' || record.gender === 'male' ? '♂️ ' : '♀️ '}
                          {translateGender(record.gender)}
                        </span>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={styles.tableCellLOS}>
                          {record.los} <span className={styles.tableCellLOSUnit}>{t('days')}</span>
                        </span>
                      </td>
                      <td className={styles.tableBodyCell}>
                        <span className={styles.tableCellMonthBadge}>
                          {record.month}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {data.records.length > 50 && (
            <div className={styles.tableInfoBanner}>
              <p className={styles.tableInfoText}>
                <span className={styles.tableInfoIcon}>ℹ️</span>
                {t('showingFirst50Records', { total: data.records.length })}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Reports;
