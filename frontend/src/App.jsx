import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './i18n/config';
import './App.css';

// Pages
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';
import Reports from './pages/Reports';

function App() {
  const { t, i18n } = useTranslation();
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
        {/* Professional Navigation Bar */}
        <nav className="navbar">
          <div className="navbar-container">
            {/* Logo & Brand */}
            <div className="navbar-brand">
              <div className="logo">
                <span className="logo-icon">🏥</span>
              </div>
              <div className="brand-text">
                <h1 className="brand-title">
                  {language === 'ar' ? 'نظام تحليل معدل الوفيات' : 'Mortality Analysis System'}
                </h1>
                <p className="brand-subtitle">
                  {language === 'ar' ? 'تحليلات طبية متقدمة' : 'Advanced Medical Analytics'}
                </p>
              </div>
            </div>

            {/* Navigation Links */}
            <div className="navbar-menu">
              <NavLink 
                to="/" 
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                end
              >
                <span className="nav-icon">📊</span>
                <span>{t('dashboard')}</span>
              </NavLink>

              <NavLink 
                to="/upload" 
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
              >
                <span className="nav-icon">📤</span>
                <span>{t('upload')}</span>
              </NavLink>

              <NavLink 
                to="/analysis" 
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
              >
                <span className="nav-icon">📈</span>
                <span>{t('analysis')}</span>
              </NavLink>

              <NavLink 
                to="/reports" 
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
              >
                <span className="nav-icon">📄</span>
                <span>{t('reports')}</span>
              </NavLink>

              {/* Language Toggle */}
              <button onClick={toggleLanguage} className="language-toggle">
                <span className="globe-icon">🌐</span>
                <span>{language === 'ar' ? 'EN' : 'ع'}</span>
              </button>
            </div>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="main-content">
          <div className="content-wrapper">
            <Routes>
              <Route path="/" element={
                <Dashboard
                  data={mortalityData}
                  totalPatients={mortalityData?.totalPatients || 0}
                  quarter={mortalityData?.quarter || ''}
                  year={mortalityData?.year || ''}
                  historyData={historyData}
                />
              } />
              <Route path="/upload" element={<Upload onDataLoaded={setMortalityData} />} />
              <Route path="/analysis" element={<Analysis data={mortalityData} />} />
              <Route path="/reports" element={<Reports data={mortalityData} language={language} />} />
            </Routes>
          </div>
        </main>

        {/* Simple Footer */}
        <footer className="footer">
          <p className="footer-text">
            {language === 'ar' 
              ? '© 2026 نظام تحليل معدل الوفيات. جميع الحقوق محفوظة.' 
              : '© 2026 Mortality Analysis System. All rights reserved.'}
          </p>
        </footer>
      </div>
    </Router>
  );
}

export default App;