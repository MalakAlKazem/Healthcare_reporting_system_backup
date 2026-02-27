import { useNavigate } from 'react-router-dom';
import styles from '../styles/Home.module.css';

function Home({ language }) {
  const navigate = useNavigate();

  return (
    <div className={styles.homeContainer}>
      {/* Hero Header */}
      <div className={styles.hero}>
        <div className={styles.heroIcon}>🏥</div>
        <h1 className={styles.heroTitle}>
          {language === 'ar'
            ? 'نظام التقارير الصحية الذكي'
            : 'Smart Healthcare Reporting System'}
        </h1>
        <p className={styles.heroSubtitle}>
          {language === 'ar'
            ? 'اختر نظام التقارير الذي تريد العمل عليه'
            : 'Select the reporting system you want to work with'}
        </p>
      </div>

      {/* System Cards */}
      <div className={styles.cardsGrid}>

        {/* Mortality Card */}
        <button
          className={`${styles.systemCard} ${styles.mortalityCard}`}
          onClick={() => navigate('/mortality/upload')}
        >
          <div className={styles.cardGlow} />
          <div className={styles.cardIcon}>💀</div>
          <h2 className={styles.cardTitle}>
            {language === 'ar' ? 'نظام تحليل معدل الوفيات' : 'Mortality Analysis System'}
          </h2>
          <p className={styles.cardDescription}>
            {language === 'ar'
              ? 'تحليل بيانات الوفيات وإنشاء تقارير إحصائية شاملة بالفصول الربعية'
              : 'Analyze mortality data and generate comprehensive quarterly statistical reports'}
          </p>
          <div className={styles.cardFeatures}>
            <span className={styles.feature}>📊 {language === 'ar' ? 'لوحة البيانات' : 'Dashboard'}</span>
            <span className={styles.feature}>📈 {language === 'ar' ? 'التحليل' : 'Analysis'}</span>
            <span className={styles.feature}>📄 {language === 'ar' ? 'التقارير' : 'Reports'}</span>
          </div>
          <div className={styles.cardCta}>
            <span>{language === 'ar' ? 'ابدأ الآن' : 'Get Started'}</span>
            <span className={styles.ctaArrow}>{language === 'ar' ? '←' : '→'}</span>
          </div>
        </button>

        {/* Medication Error Card */}
        <button
          className={`${styles.systemCard} ${styles.medicationCard}`}
          onClick={() => navigate('/medication/upload')}
        >
          <div className={styles.cardGlow} />
          <div className={styles.cardIcon}>💊</div>
          <h2 className={styles.cardTitle}>
            {language === 'ar' ? 'نظام الإبلاغ عن أخطاء الدواء' : 'Medication Error Reporting'}
          </h2>
          <p className={styles.cardDescription}>
            {language === 'ar'
              ? 'رصد وتحليل أخطاء الدواء وإصدار تقارير الجودة والسلامة الدوائية'
              : 'Monitor and analyze medication errors, generate quality and drug safety reports'}
          </p>
          <div className={styles.cardFeatures}>
            <span className={styles.feature}>📊 {language === 'ar' ? 'لوحة البيانات' : 'Dashboard'}</span>
            <span className={styles.feature}>📉 {language === 'ar' ? 'معدل الخطأ' : 'Error Rate'}</span>
            <span className={styles.feature}>📄 {language === 'ar' ? 'التقارير' : 'Reports'}</span>
          </div>
          <div className={styles.cardCta}>
            <span>{language === 'ar' ? 'ابدأ الآن' : 'Get Started'}</span>
            <span className={styles.ctaArrow}>{language === 'ar' ? '←' : '→'}</span>
          </div>
        </button>

        {/* Infection Control Card */}
        <div className={`${styles.systemCard} ${styles.infectionCard}`}>
          <div className={styles.cardGlow} />
          <div className={styles.cardIcon}>🦠</div>
          <h2 className={styles.cardTitle}>
            {language === 'ar' ? 'نظام مكافحة العدوى' : 'Infection Control System'}
          </h2>
          <p className={styles.cardDescription}>
            {language === 'ar'
              ? 'رصد وتحليل مؤشرات مكافحة العدوى (VAP, CLABSI, CAUTI) وإصدار تقارير الوقاية'
              : 'Monitor and analyze infection control indicators (VAP, CLABSI, CAUTI) and generate prevention reports'}
          </p>
          <div className={styles.cardFeatures}>
            <button
              className={styles.indicatorBtn}
              onClick={() => navigate('/vap/upload')}
            >
              🫁 VAP
            </button>
            <button
              className={styles.indicatorBtn}
              onClick={() => navigate('/clabsi/upload')}
            >
              🩸 CLABSI
            </button>
            <button className={`${styles.indicatorBtn} ${styles.indicatorBtnDisabled}`} disabled>
              🧪 CAUTI
            </button>
          </div>
        </div>

      </div>

      {/* Footer note */}
      <p className={styles.homeNote}>
        {language === 'ar'
          ? 'يمكنك التبديل بين الأنظمة في أي وقت من خلال شعار التطبيق'
          : 'You can switch between systems at any time via the app logo'}
      </p>
    </div>
  );
}

export default Home;
