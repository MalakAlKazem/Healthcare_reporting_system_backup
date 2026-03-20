import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import styles from '../styles/Upload.module.css';

const API_URL = 'http://localhost:8000/api/medication';

const quarters = [
  { value: 'الفصل الأول', label: 'الفصل الأول / Q1' },
  { value: 'الفصل الثاني', label: 'الفصل الثاني / Q2' },
  { value: 'الفصل الثالث', label: 'الفصل الثالث / Q3' },
  { value: 'الفصل الرابع', label: 'الفصل الرابع / Q4' },
];

function MedicationUpload({ language }) {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [fileName, setFileName] = useState('');
  const [quarter, setQuarter] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [totalDoses, setTotalDoses] = useState('');

  const ar = language === 'ar';

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!quarter) {
      setError(ar ? 'يرجى اختيار الفصل' : 'Please select a quarter');
      return;
    }
    if (!totalDoses || parseInt(totalDoses) <= 0) {
      setError(ar ? 'يرجى إدخال إجمالي الجرعات الدوائية' : 'Please enter the total number of doses dispensed');
      return;
    }

    setFileName(file.name);
    setUploading(true);
    setError(null);
    setSuccess(false);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('quarter', quarter);
    formData.append('year', year);
    if (totalDoses && parseInt(totalDoses) > 0) {
      formData.append('total_doses', parseInt(totalDoses));
    }

    try {
      const response = await axios.post(`${API_URL}/process-data`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          setProgress(Math.round((e.loaded * 100) / e.total));
        },
      });


      setSuccess(true);
      setUploading(false);
      setTimeout(() => navigate('/medication/dashboard'), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || (ar ? 'حدث خطأ أثناء رفع الملف' : 'Upload error occurred'));
      setUploading(false);
      setProgress(0);
    }
  }, [ navigate, quarter, year, totalDoses, ar]);

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
      {/* Header */}
      <div className={styles.uploadHeader} style={{ background: 'linear-gradient(135deg, #0d9488 0%, #0891b2 50%, #0e7490 100%)' }}>
        <div className={styles.headerContent}>
          <div className={styles.headerIcon}>💊</div>
          <div className={styles.headerText}>
            <h2>{ar ? 'رفع بيانات أخطاء الدواء' : 'Upload Medication Error Data'}</h2>
            <p>{ar ? 'ارفع ملف Excel يحتوي على بيانات الفصل الربعي' : 'Upload an Excel file with quarterly medication error data'}</p>
          </div>
        </div>
      </div>

      <div className={styles.uploadCard}>
        {/* Quarter & Year */}
        <div className={styles.inputSection}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label className={styles.inputLabel}>
                <span className={styles.inputIcon}>📅</span>
                <span>{ar ? 'الفصل / Quarter' : 'Quarter'}</span>
              </label>
              <select
                value={quarter}
                onChange={(e) => setQuarter(e.target.value)}
                className={styles.inputField}
                disabled={uploading}
              >
                <option value="">{ar ? '-- اختر الفصل --' : '-- Select Quarter --'}</option>
                {quarters.map((q) => (
                  <option key={q.value} value={q.value}>{q.label}</option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label className={styles.inputLabel}>
                <span className={styles.inputIcon}>📆</span>
                <span>{ar ? 'السنة / Year' : 'Year'}</span>
              </label>
              <input
                type="number"
                min="2020"
                max="2030"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className={styles.inputField}
                disabled={uploading}
              />
            </div>
          </div>
        </div>

        {/* Total Doses */}
        <div className={styles.inputSection}>
          <label className={styles.inputLabel}>
            <span className={styles.inputIcon}>💉</span>
            <span>{ar ? 'إجمالي الجرعات الدوائية / Total Doses' : 'Total Doses Dispensed'}</span>
          </label>
          <input
            type="number"
            min="1"
            placeholder={ar ? 'أدخل عدد الجرعات (اختياري إذا موجود في الملف)' : 'Enter total doses (optional if present in file)'}
            value={totalDoses}
            onChange={(e) => setTotalDoses(e.target.value)}
            className={styles.inputField}
            disabled={uploading}
          />
          <p className={styles.inputHint}>
            {ar
              ? '* مطلوب — إذا وُجد الرقم في الملف أيضاً سيتم استخدامه تلقائياً، وإلا سيُستخدم الرقم المُدخل هنا'
              : '* Required — if also found in the Excel file it will be used automatically, otherwise this value is used'}
          </p>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`${styles.dropzone} ${isDragActive ? styles.dropzoneActive : ''} ${uploading ? styles.dropzoneUploading : ''}`}
        >
          <input {...getInputProps()} />
          <div className={styles.dropzoneIcon}>📊</div>

          {uploading ? (
            <div className={styles.uploadProgress}>
              <div className={styles.progressTitle}>{ar ? 'جارٍ المعالجة...' : 'Processing...'}</div>
              <div className={styles.progressBar}>
                <div className={styles.progressFill} style={{ width: `${progress}%` }} />
              </div>
              <div className={styles.progressText}>{progress}%</div>
              {fileName && <div className={styles.fileName}>{fileName}</div>}
            </div>
          ) : isDragActive ? (
            <div className={styles.dropzoneContent}>
              <p className={styles.dropzoneTitle}>{ar ? 'أفلت الملف هنا' : 'Drop the file here'}</p>
            </div>
          ) : (
            <div className={styles.dropzoneContent}>
              <p className={styles.dropzoneTitle}>{ar ? 'اسحب وأفلت الملف هنا' : 'Drag & drop your file here'}</p>
              <p className={styles.dropzoneSeparator}>{ar ? 'أو' : 'or'}</p>
              <button className={styles.browseButton} style={{ background: 'linear-gradient(135deg, #0d9488 0%, #0891b2 100%)' }}>
                {ar ? 'استعرض الملفات' : 'Browse Files'}
              </button>
              <p className={styles.acceptedFormats}>{ar ? 'الصيغ المقبولة' : 'Accepted formats'}: Excel (.xlsx, .xls)</p>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className={`${styles.alert} ${styles.alertError}`}>
            <div className={styles.alertContent}>
              <div className={styles.alertIcon}>❌</div>
              <div className={styles.alertText}>
                <p className={styles.alertTitle}>{ar ? 'خطأ' : 'Error'}</p>
                <p className={styles.alertDescription}>{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success */}
        {success && (
          <div className={`${styles.alert} ${styles.alertSuccess}`}>
            <div className={styles.alertContent}>
              <div className={styles.alertIcon}>✅</div>
              <div className={styles.alertText}>
                <p className={styles.alertTitle}>{ar ? 'تم بنجاح' : 'Success'}</p>
                <p className={styles.alertDescription}>{ar ? 'تمت معالجة البيانات بنجاح' : 'Data processed successfully'}</p>
                <p className={styles.alertSubtext}>
                  <span className={styles.redirectSpinner}>⏳</span>
                  {ar ? 'جارٍ التحويل إلى لوحة البيانات...' : 'Redirecting to dashboard...'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className={styles.instructions} style={{ background: 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 50%, #cffafe 100%)', borderColor: '#5eead4' }}>
          <div className={styles.instructionsHeader}>
            <div className={styles.instructionsIcon} style={{ background: 'linear-gradient(135deg, #0d9488 0%, #0891b2 100%)' }}>💡</div>
            <h3 className={styles.instructionsTitle} style={{ color: '#0f766e' }}>
              {ar ? 'تعليمات الاستخدام' : 'Instructions'}
            </h3>
          </div>
          <div className={styles.instructionsList}>
            {[
              ar ? 'اختر الفصل والسنة وأدخل عدد الجرعات إذا لزم الأمر' : 'Select quarter, year, and enter total doses if needed',
              ar ? 'اسحب ملف Excel وأفلته أو انقر للاستعراض' : 'Drag and drop the Excel file or click to browse',
              ar ? 'سيتم معالجة البيانات تلقائياً وحفظها' : 'Data will be processed and saved automatically',
              ar ? 'اذهب إلى تبويب التقارير لتوليد وتحميل تقرير Word' : 'Go to the Reports tab to generate and download a Word report',
            ].map((text, i) => (
              <div key={i} className={styles.instructionItem}>
                <div className={styles.instructionNumber}>{i + 1}</div>
                <p className={styles.instructionText}>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MedicationUpload;
