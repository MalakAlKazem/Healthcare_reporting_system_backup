import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import styles from '../styles/Upload.module.css';

const API_URL = 'http://localhost:8000/api/vap';

const quarters = [
  { value: 1, label: 'الفصل الأول / Q1' },
  { value: 2, label: 'الفصل الثاني / Q2' },
  { value: 3, label: 'الفصل الثالث / Q3' },
  { value: 4, label: 'الفصل الرابع / Q4' },
];

function VapUpload({ language }) {
  const navigate = useNavigate();
  const ar = language === 'ar';

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [fileName, setFileName] = useState('');
  const [quarter, setQuarter] = useState('');
  const [year, setYear] = useState(new Date().getFullYear());

  const departments = ["ICU", "CCU", "CSU", "ICN", "Pediatric", "ITU"];

  const [denominators, setDenominators] = useState({
    ICU: "",
    CCU: "",
    CSU: "",
    ICN: "",
    Pediatric: "",
    ITU: ""
  });

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!quarter) {
      setError(ar ? 'يرجى اختيار الفصل' : 'Please select a quarter');
      return;
    }

    for (let dept of departments) {
      if (!denominators[dept] || Number(denominators[dept]) <= 0) {
        setError(
          ar
            ? `يرجى إدخال أيام جهاز التنفس لقسم ${dept}`
            : `Please enter ventilator days for ${dept}`
        );
        return;
      }
    }

    setFileName(file.name);
    setUploading(true);
    setError(null);
    setSuccess(false);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('year', year);
    formData.append('quarter', quarter);

    formData.append('icu_days', Number(denominators.ICU));
    formData.append('ccu_days', Number(denominators.CCU));
    formData.append('csu_days', Number(denominators.CSU));
    formData.append('ped_days', Number(denominators.Pediatric));
    formData.append('icn_days', Number(denominators.ICN));
    formData.append('itu_days', Number(denominators.ITU));

    try {
      await axios.post(`${API_URL}/process-data`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          setProgress(Math.round((e.loaded * 100) / e.total));
        },
      });

      setSuccess(true);
      setUploading(false);

      setTimeout(() => {
        navigate('/vap/dashboard');
      }, 2000);

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        (ar ? 'حدث خطأ أثناء رفع الملف' : 'Upload error occurred')
      );
      setUploading(false);
      setProgress(0);
    }
  }, [quarter, year, navigate, ar, denominators]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div className={styles.uploadContainer}>

      <div
        className={styles.uploadHeader}
        style={{ background: 'linear-gradient(135deg, #0f766e 0%, #14b8a6 50%, #0d9488 100%)' }}
      >
        <div className={styles.headerContent}>
          <div className={styles.headerIcon}>🫁</div>
          <div className={styles.headerText}>
            <h2>{ar ? 'رفع بيانات VAP' : 'Upload VAP Data'}</h2>
            <p>
              {ar
                ? 'ارفع ملف Excel يحتوي على بيانات حالات VAP'
                : 'Upload an Excel file containing VAP case data'}
            </p>
          </div>
        </div>
      </div>

      <div className={styles.uploadCard}>

        {/* Quarter & Year */}
        <div className={styles.inputSection}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label className={styles.inputLabel}>
                📅 {ar ? 'الفصل' : 'Quarter'}
              </label>
              <select
                value={quarter}
                onChange={(e) => setQuarter(Number(e.target.value))}
                className={styles.inputField}
                disabled={uploading}
              >
                <option value="">
                  {ar ? '-- اختر الفصل --' : '-- Select Quarter --'}
                </option>
                {quarters.map((q) => (
                  <option key={q.value} value={q.value}>
                    {q.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ flex: 1, minWidth: '200px' }}>
              <label className={styles.inputLabel}>
                📆 {ar ? 'السنة' : 'Year'}
              </label>
              <input
                type="number"
                min="2020"
                max="2035"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className={styles.inputField}
                disabled={uploading}
              />
            </div>
          </div>
        </div>

        {/* Ventilator Days */}
        <div className={styles.inputSection}>
          <label className={styles.inputLabel}>
            🏥 {ar ? 'أيام جهاز التنفس لكل قسم' : 'Ventilator Days per Department'}
          </label>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            {departments.map((dept) => (
              <div key={dept}>
                <label style={{ fontSize: 13, fontWeight: 600 }}>
                  {dept}
                </label>
                <input
                  type="number"
                  min="0"
                  value={denominators[dept]}
                  onChange={(e) =>
                    setDenominators({
                      ...denominators,
                      [dept]: e.target.value
                    })
                  }
                  className={styles.inputField}
                  disabled={uploading}
                  placeholder={ar ? 'أدخل الأيام' : 'Enter days'}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Dropzone (unchanged) */}
        <div
          {...getRootProps()}
          className={`${styles.dropzone} ${isDragActive ? styles.dropzoneActive : ''} ${uploading ? styles.dropzoneUploading : ''}`}
        >
          <input {...getInputProps()} />
          <div className={styles.dropzoneIcon}>📊</div>

          {uploading ? (
            <div className={styles.uploadProgress}>
              <div className={styles.progressTitle}>
                {ar ? 'جارٍ المعالجة...' : 'Processing...'}
              </div>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className={styles.progressText}>{progress}%</div>
              {fileName && <div className={styles.fileName}>{fileName}</div>}
            </div>
          ) : isDragActive ? (
            <div className={styles.dropzoneContent}>
              <p className={styles.dropzoneTitle}>
                {ar ? 'أفلت الملف هنا' : 'Drop the file here'}
              </p>
            </div>
          ) : (
            <div className={styles.dropzoneContent}>
              <p className={styles.dropzoneTitle}>
                {ar ? 'اسحب وأفلت الملف هنا' : 'Drag & drop your file here'}
              </p>
              <p className={styles.dropzoneSeparator}>
                {ar ? 'أو' : 'or'}
              </p>
              <button
                className={styles.browseButton}
                style={{ background: 'linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)' }}
              >
                {ar ? 'استعرض الملفات' : 'Browse Files'}
              </button>
              <p className={styles.acceptedFormats}>
                {ar ? 'الصيغ المقبولة' : 'Accepted formats'}: Excel (.xlsx, .xls)
              </p>
            </div>
          )}
        </div>

        {error && (
          <div className={`${styles.alert} ${styles.alertError}`}>
            ❌ {error}
          </div>
        )}

        {success && (
          <div className={`${styles.alert} ${styles.alertSuccess}`}>
            ✅ {ar ? 'تمت معالجة البيانات بنجاح' : 'Data processed successfully'}
          </div>
        )}

      </div>
    </div>
  );
}

export default VapUpload;