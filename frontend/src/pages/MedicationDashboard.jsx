import { useNavigate } from 'react-router-dom';

function MedicationDashboard({ data, language }) {
  const navigate = useNavigate();
  const ar = language === 'ar';

  if (!data) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: '1.5rem',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '5rem' }}>💊</div>
        <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#1e293b' }}>
          {ar ? 'لا توجد بيانات' : 'No Data Available'}
        </h2>
        <p style={{ color: '#64748b', fontSize: '1.05rem', maxWidth: '420px' }}>
          {ar
            ? 'يرجى رفع ملف بيانات أخطاء الدواء أولاً لعرض النتائج'
            : 'Please upload a medication error data file first to view results'}
        </p>
        <button
          onClick={() => navigate('/medication/upload')}
          style={{
            background: 'linear-gradient(135deg, #0d9488, #0891b2)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            padding: '0.875rem 2.5rem',
            fontSize: '1rem',
            fontWeight: '700',
            cursor: 'pointer',
            boxShadow: '0 8px 25px rgba(13, 148, 136, 0.35)',
          }}
        >
          📤 {ar ? 'رفع البيانات' : 'Upload Data'}
        </button>
      </div>
    );
  }

  const stats = data.statistics || {};
  const summary = stats.summary || {};

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #0d9488 0%, #0891b2 50%, #0e7490 100%)',
        borderRadius: '24px',
        padding: '2.5rem 3rem',
        marginBottom: '2rem',
        color: 'white',
        boxShadow: '0 20px 60px rgba(13, 148, 136, 0.3)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ fontSize: '3.5rem' }}>💊</div>
          <div>
            <h2 style={{ fontSize: '2rem', fontWeight: '900', margin: 0 }}>
              {ar ? 'لوحة بيانات أخطاء الدواء' : 'Medication Error Dashboard'}
            </h2>
            <p style={{ margin: '0.4rem 0 0', color: 'rgba(255,255,255,0.85)', fontSize: '1rem' }}>
              {data.quarter} {data.year}
            </p>
          </div>
        </div>
      </div>

      {/* Under Construction */}
      <div style={{
        background: 'white',
        borderRadius: '24px',
        padding: '5rem 3rem',
        textAlign: 'center',
        boxShadow: '0 10px 40px rgba(0,0,0,0.08)',
        border: '1px solid #e2e8f0',
      }}>
        <div style={{ fontSize: '5rem', marginBottom: '1.5rem' }}>🚧</div>
        <h3 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#1e293b', marginBottom: '1rem' }}>
          {ar ? 'قيد التطوير' : 'Under Development'}
        </h3>
        <p style={{ color: '#64748b', fontSize: '1.05rem', maxWidth: '500px', margin: '0 auto 2rem' }}>
          {ar
            ? 'سيتم إضافة الرسوم البيانية ومؤشرات الأداء قريباً. يمكنك الآن تحميل التقرير من صفحة التقارير.'
            : 'Charts and KPI indicators will be added soon. You can download the report from the Reports page now.'}
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => navigate('/medication/reports')}
            style={{
              background: 'linear-gradient(135deg, #0d9488, #0891b2)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              padding: '0.875rem 2.5rem',
              fontSize: '1rem',
              fontWeight: '700',
              cursor: 'pointer',
              boxShadow: '0 8px 25px rgba(13, 148, 136, 0.3)',
            }}
          >
            📄 {ar ? 'الذهاب إلى التقارير' : 'Go to Reports'}
          </button>
          <button
            onClick={() => navigate('/medication/upload')}
            style={{
              background: 'white',
              color: '#0d9488',
              border: '2px solid #0d9488',
              borderRadius: '12px',
              padding: '0.875rem 2.5rem',
              fontSize: '1rem',
              fontWeight: '700',
              cursor: 'pointer',
            }}
          >
            📤 {ar ? 'رفع بيانات جديدة' : 'Upload New Data'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default MedicationDashboard;
