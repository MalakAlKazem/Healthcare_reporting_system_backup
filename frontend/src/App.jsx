import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './i18n/config';
import './App.css';

// Pages
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Reports from './pages/Reports';
import MedicationUpload from './pages/MedicationUpload';
import MedicationDashboard from './pages/MedicationDashboard';
import MedicationReports from './pages/MedicationReports';
import VapUpload from './pages/VapUpload';
import VapDashboard from './pages/VapDashboard';
import VapReports from './pages/VapReports';
import ClabsiUpload from './pages/ClabsiUpload';
import ClabsiDashboard from './pages/ClabsiDashboard';

// ─── Navbar: changes based on current route section ────────────────────────
function Navbar({ language, toggleLanguage }) {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const ar = language === 'ar';

  const isMortality = location.pathname.startsWith('/mortality');
  const isMedication = location.pathname.startsWith('/medication');
  const isVap = location.pathname.startsWith('/vap');
  const isClabsi = location.pathname.startsWith('/clabsi');
  const isHome = location.pathname === '/';

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo & Brand — always links to home */}
        <button
          className="navbar-brand"
          onClick={() => navigate('/')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          <div className="logo">
            <span className="logo-icon">🏥</span>
          </div>
          <div className="brand-text">
            <h1 className="brand-title">
              {isMortality
                ? (ar ? 'نظام تحليل معدل الوفيات' : 'Mortality Analysis System')
                : isMedication
                  ? (ar ? 'نظام أخطاء الدواء' : 'Medication Error System')
                  : isVap
                    ? (ar ? 'نظام مكافحة العدوى' : 'Infection Control System')
                    : isClabsi
                      ? (ar ? 'نظام مكافحة العدوى' : 'Infection Control System')
                      : (ar ? 'نظام التقارير الصحية' : 'Healthcare Reporting System')}
            </h1>
            <p className="brand-subtitle">
              {ar ? 'تحليلات طبية متقدمة' : 'Advanced Medical Analytics'}
            </p>
          </div>
        </button>

        <div className="navbar-menu">
          {/* Home: no section links */}
          {isHome && null}

          {/* Mortality section links */}
          {isMortality && (
            <>
              <NavLink to="/mortality/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📊</span>
                <span>{t('dashboard')}</span>
              </NavLink>
              <NavLink to="/mortality/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📤</span>
                <span>{t('upload')}</span>
              </NavLink>
              <NavLink to="/mortality/reports" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📄</span>
                <span>{t('reports')}</span>
              </NavLink>
            </>
          )}

          {/* VAP / Infection Control section links */}
          {isVap && (
            <>
              <NavLink to="/vap/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📊</span>
                <span>{ar ? 'لوحة البيانات' : 'Dashboard'}</span>
              </NavLink>
              <NavLink to="/vap/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📤</span>
                <span>{ar ? 'رفع البيانات' : 'Upload'}</span>
              </NavLink>
              <NavLink to="/vap/reports" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📄</span>
                <span>{ar ? 'التقارير' : 'Reports'}</span>
              </NavLink>
            </>
          )}

          {/* CLABSI / Infection Control section links */}
          {isClabsi && (
            <>
              <NavLink to="/clabsi/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📊</span>
                <span>{ar ? 'لوحة البيانات' : 'Dashboard'}</span>
              </NavLink>
              <NavLink to="/clabsi/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📤</span>
                <span>{ar ? 'رفع البيانات' : 'Upload'}</span>
              </NavLink>
            </>
          )}

          {/* Medication section links */}
          {isMedication && (
            <>
              <NavLink to="/medication/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📊</span>
                <span>{ar ? 'لوحة البيانات' : 'Dashboard'}</span>
              </NavLink>
              <NavLink to="/medication/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📤</span>
                <span>{ar ? 'رفع البيانات' : 'Upload'}</span>
              </NavLink>
              <NavLink to="/medication/reports" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-icon">📄</span>
                <span>{ar ? 'التقارير' : 'Reports'}</span>
              </NavLink>
            </>
          )}

          {/* Language Toggle */}
          <button onClick={toggleLanguage} className="language-toggle">
            <span className="globe-icon">🌐</span>
            <span>{language === 'ar' ? 'EN' : 'ع'}</span>
          </button>
        </div>
      </div>
    </nav>
  );
}

// ─── Main App ───────────────────────────────────────────────────────────────
function App() {
  const { i18n } = useTranslation();
  const [language, setLanguage] = useState('ar');
  const [mortalityData, setMortalityData] = useState(null);
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
    document.body.lang = language;
  }, [language]);

  useEffect(() => {
    fetch('http://localhost:8000/api/history')
      .then(res => res.json())
      .then(data => setHistoryData(data))
      .catch(err => console.error('Failed to load history:', err));
  }, []);

  const toggleLanguage = () => {
    const newLang = language === 'ar' ? 'en' : 'ar';
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  return (
    <Router>
      <div className="app">
        <Navbar language={language} toggleLanguage={toggleLanguage} />

        <main className="main-content">
          <div className="content-wrapper">
            <Routes>
              {/* ── Home: system selector ── */}
              <Route path="/" element={<Home language={language} />} />

              {/* ── Mortality system ── */}
              <Route path="/mortality/dashboard" element={
                <Dashboard
                  data={mortalityData}
                  totalPatients={mortalityData?.totalPatients || 0}
                  quarter={mortalityData?.quarter || ''}
                  year={mortalityData?.year || ''}
                  historyData={historyData}
                />
              } />
              <Route path="/mortality/upload" element={
                <Upload onDataLoaded={setMortalityData} />
              } />
              <Route path="/mortality/reports" element={
                <Reports data={mortalityData} language={language} />
              } />

              {/* ── Infection Control / VAP system ── */}
              <Route path="/vap/upload" element={<VapUpload language={language} />} />
              <Route path="/vap/dashboard" element={<VapDashboard language={language} />} />
              <Route path="/vap/reports" element={<VapReports language={language} />} />

              {/* ── Infection Control / CLABSI system ── */}
              <Route path="/clabsi/upload" element={<ClabsiUpload language={language} />} />
              <Route path="/clabsi/dashboard" element={<ClabsiDashboard language={language} />} />

              {/* ── Medication Error system ── */}
              <Route path="/medication/upload" element={
                  <MedicationUpload language={language} />
                } />

                <Route path="/medication/dashboard" element={
                  <MedicationDashboard language={language} />
                } />

                <Route path="/medication/reports" element={
                  <MedicationReports language={language} />
                } />
              </Routes>
          </div>
        </main>

        <footer className="footer">
          <p className="footer-text">
            {language === 'ar'
              ? '© 2026 نظام التقارير الصحية الذكي. جميع الحقوق محفوظة.'
              : '© 2026 Smart Healthcare Reporting System. All rights reserved.'}
          </p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
