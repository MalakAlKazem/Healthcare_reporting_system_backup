# Smart Healthcare Reporting System
## Complete Offline Transfer & Installation Guide

> **What this guide covers:** Moving the fully working system from your online PC to a completely offline PC (or virtual machine) — frontend, Python backend, and Qwen 2.5-7B AI model — with no internet connection on the target machine.

---

## Table of Contents

- [System Components](#system-components)
- [Transfer Size Summary](#transfer-size-summary)
- [Why Node.js Must Be Installed](#why-nodejs-must-be-installed-even-with-node_modules-present)
- [Hardware Requirements for the AI Model](#hardware-requirements-for-the-ai-model)
  - [Option A — NVIDIA GPU](#option-a--nvidia-gpu-recommended)
  - [Option B — CPU Only](#option-b--cpu-only-no-gpu-required)
  - [Model File Options](#model-file-options)
- [PART 1 — Steps on Your Online PC](#part-1--steps-on-your-online-pc)
  - [Step 1 — Bundle Python Packages](#step-1--bundle-python-packages)
  - [Step 2 — Bundle llama-cpp-python](#step-2--bundle-llama-cpp-python-choose-one)
  - [Step 3 — Copy the AI Model File](#step-3--copy-the-ai-model-file)
  - [Step 4 — Copy the Project Folder](#step-4--copy-the-project-folder)
  - [Step 5 — Download Installer Files](#step-5--download-installer-files)
  - [Step 6 — Download CUDA Toolkit (GPU Only)](#step-6--download-cuda-toolkit-gpu-only)
  - [Final Transfer Folder Structure](#final-transfer-folder-structure)
- [PART 2 — Steps on the Offline PC](#part-2--steps-on-the-offline-pc)
  - [Step 1 — Install Python 3.11.9](#step-1--install-python-3119)
  - [Step 2 — Install Node.js v24.11.0](#step-2--install-nodejs-v24110)
  - [Step 3 — Install CUDA Drivers (GPU Only)](#step-3--install-cuda-drivers-gpu-only--skip-for-cpu)
  - [Step 4 — Copy Project Files](#step-4--copy-project-files)
  - [Step 5 — Create Python Virtual Environment](#step-5--create-python-virtual-environment)
  - [Step 6 — Install llama-cpp-python](#step-6--install-llama-cpp-python)
  - [Step 7 — Place the AI Model File](#step-7--place-the-ai-model-file)
  - [Step 8 — Configure .env](#step-8--configure-env)
  - [Step 9 — Configure GPU vs CPU in ai_service.py](#step-9--configure-gpu-vs-cpu-in-ai_servicepy)
- [PART 3 — Running the System](#part-3--running-the-system)
- [PART 4 — Verification & Troubleshooting](#part-4--verification--troubleshooting)
  - [Verification Checklist](#verification-checklist)
  - [Troubleshooting](#troubleshooting)

---

## System Components

| Component | Technology | Port | Required? |
|-----------|-----------|------|-----------|
| Frontend | React 19 + Vite | 5173 | Always |
| Backend | Python 3.11.9 + FastAPI + Uvicorn | 8000 | Always |
| AI Analysis | llama-cpp-python + Qwen 2.5-7B GGUF | — | Optional |

> **Note:** The system runs fully without AI. Set `ENABLE_AI=false` in `.env` to skip AI setup entirely.

---

## Transfer Size Summary

| Item | Size | How to Transfer |
|------|------|----------------|
| Python 3.11.9 installer | ~30 MB | Telegram or USB |
| Node.js v24.11.0 installer | ~30 MB | Telegram or USB |
| Python `.whl` packages | ~500 MB | USB / Google Drive |
| Project folder + `node_modules` | ~400 MB | USB / Google Drive |
| AI model (`.gguf`) | ~3.4 GB | USB / Google Drive |
| CUDA Toolkit (GPU only) | ~3 GB | USB / Google Drive |
| **TOTAL with GPU** | **~7–8 GB** | USB drive |
| **TOTAL CPU only** | **~4–5 GB** | USB drive |

> **Tip:** The two small installers (~30 MB each) can be sent via Telegram. Pack everything else onto a USB drive.

---

## Why Node.js Must Be Installed (Even with `node_modules` Present)

The project folder already contains `node_modules\` — which means all frontend packages (React, Vite, etc.) are already there. **However, Node.js itself still must be installed on the offline PC.**

`node_modules` contains the *packages*, but **not the Node.js runtime** (`node.exe`). When `start_frontend.bat` runs:

```bat
node node_modules\.bin\vite
```

Windows needs to find `node.exe` somewhere on the system PATH. Without the Node.js installer, Windows has no idea what `node` means and the command fails immediately with:

```
'node' is not recognized as an internal or external command
```

The installer is only ~30 MB — small enough to send via Telegram alongside the Python installer.

---

## Hardware Requirements for the AI Model

The AI model (Qwen 2.5-7B) runs on either an NVIDIA GPU or CPU only. **Both options use the exact same `.gguf` model file** — only the `llama-cpp-python` build differs.

### Option A — NVIDIA GPU (Recommended)

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| GPU | NVIDIA with 6 GB VRAM (e.g. RTX 3060) | RTX 4060 or better |
| CUDA | Version 11.8 | Version 12.x |
| System RAM | 16 GB | 16 GB |
| Storage | 20 GB free | 30 GB free |
| OS | Windows 10/11 | Windows 11 / Ubuntu 20.04+ |

> **GPU performance:** ~2–5 seconds per AI paragraph. Full report generation takes 30–45 seconds.

### Option B — CPU Only (No GPU Required)

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | Modern multi-core (Intel i5/i7, AMD Ryzen 5/7) | 8+ cores |
| System RAM | 16 GB (model uses ~4–5 GB RAM) | 32 GB |
| Storage | 20 GB free | 30 GB free |
| OS | Windows 10/11 | Windows 11 / Linux |

> **CPU performance:** ~30–90 seconds per AI paragraph. If speed matters, set `ENABLE_AI=false` and skip the model entirely.

### Model File Options

Both GPU and CPU use the same `.gguf` file — choose based on available VRAM or RAM:

| Model File | Size | VRAM / RAM Needed | Speed | Quality | Best For |
|------------|------|-------------------|-------|---------|----------|
| `q3_k_m.gguf` | 3.4 GB | 4–5 GB | Fast | Good | GPU 6 GB / CPU 16 GB — **this project** |
| `q4_0.gguf` | 4.1 GB | 5 GB | Fast | Good | CPU 16 GB RAM |
| `q4_k_m.gguf` | 4.7 GB | 6 GB | Medium | Better | GPU 6 GB / CPU 16 GB |
| `q5_k_m.gguf` | 5.3 GB | 6.5 GB | Slower | Great | GPU 8 GB |
| `q8_0.gguf` | 7.7 GB | 9 GB | Slowest | Best | GPU 10 GB / CPU 32 GB |

> **This project uses:** `qwen2.5-7b-instruct-q3_k_m.gguf` — the smallest and fastest option, well suited for a 6 GB GPU. If the offline PC is CPU-only, `q4_k_m.gguf` gives a better quality/speed balance at the cost of ~1 GB extra RAM.

---

---

# PART 1 — Steps on Your Online PC

Complete all steps below on the machine that has internet. The goal is to pack everything into a transfer folder, then move it to the offline PC via USB.

---

## Step 1 — Bundle Python Packages

From your project folder, download all required `.whl` files:

```powershell
cd C:\Users\pc\Desktop\Healthcare_reporting_system_backup\python-service

# Use the Python 3.11 venv already in your project
.\venv311\Scripts\pip.exe download -r requirements.txt -d C:\TransferFolder\offline_packages
```

> **Why `pip download` and not `pip install`?**
> Your original install commands used `pip install` — that installs packages directly onto the current machine. Here we use `pip download -d <folder>` instead, which saves the `.whl` files into a folder without installing anything. Those files are then carried to the offline PC and installed there. The index URLs (`--extra-index-url`, `--index-url`) point to the same sources in both cases — the only difference is *download for transfer* vs *install immediately*.

---

## Step 2 — Bundle llama-cpp-python (Choose One)

> **Important:** Your current `llama-cpp-python` was installed with CUDA 12.2. That build will crash on a CPU-only machine. Download the correct build for your offline PC — or download both if you are not sure yet.

First, check your CUDA version on the online PC:

```powershell
nvcc --version
# Look for: release 12.2  (or whatever version you have)
```

> **Why no version number like `==0.3.4`?**
> Your original install commands didn't pin any version — pip just grabbed the latest compatible build. The download commands below do the same, so whatever version is already installed and working on your online PC is exactly what gets packaged for the offline PC. Pinning a specific version could accidentally download a *different* version than the one you already tested.

### Option A — CPU-only build

```powershell
pip download llama-cpp-python --no-deps -d C:\TransferFolder\llama_cpu `
  --index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

### Option B — GPU/CUDA build (match your CUDA version)

```powershell
# For CUDA 12.2 (replace cu122 with your version, e.g. cu118 for CUDA 11.8)
.\venv311\Scripts\pip.exe download llama-cpp-python --no-deps `
  -d C:\TransferFolder\llama_gpu `
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
```

> **CUDA version tag reference:** `cu118` = CUDA 11.8 · `cu121` = CUDA 12.1 · `cu122` = CUDA 12.2 · `cu123` = CUDA 12.3. Match the tag to what `nvcc --version` reported.

> **Not sure about the offline PC's GPU?** Download both `llama_cpu\` and `llama_gpu\` now while you have internet. On the offline PC you will only install one — whichever matches the hardware.

---

## Step 3 — Copy the AI Model File

Copy your existing `.gguf` model file into the transfer folder:

```
C:\TransferFolder\model\qwen2.5-7b-instruct-q3_k_m.gguf
```

> **For CPU-only offline PC:** Consider also downloading `qwen2.5-7b-instruct-q4_k_m.gguf` from HuggingFace — it gives slightly better quality on CPU at the cost of ~1 GB extra RAM. Same destination folder.

---

## Step 4 — Copy the Project Folder

Copy your entire `Healthcare_reporting_system_backup\` folder into `C:\TransferFolder\Healthcare_reporting_system_backup\`.

> **Important:** Make sure `frontend\node_modules\` **IS included**. Do not skip it — the offline PC will use it directly without running `npm install`.

---

## Step 5 — Download Installer Files

Download these two files and place them in `C:\TransferFolder\installers\`:

| File | Download URL |
|------|-------------|
| `python-3.11.9-amd64.exe` | https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe |
| `node-v24.11.0-x64.msi` | https://nodejs.org/dist/v24.11.0/node-v24.11.0-x64.msi |

> **Tip:** Both are ~30 MB — small enough to send via Telegram. Everything else goes on USB.

---

## Step 6 — Download CUDA Toolkit (GPU Only)

If the offline PC has an NVIDIA GPU, download one of these:

| Version | Windows Download |
|---------|-----------------|
| CUDA 11.8 (safer, wider support) | https://developer.nvidia.com/cuda-11-8-0-download-archive (~3 GB) |
| CUDA 12.2 (matches your current install) | https://developer.nvidia.com/cuda-12-2-0-download-archive (~3.5 GB) |

Skip this step entirely if the offline PC is CPU-only.

---

## Final Transfer Folder Structure

```
TransferFolder\
├── installers\
│   ├── python-3.11.9-amd64.exe                  ← send via Telegram
│   └── node-v24.11.0-x64.msi                    ← send via Telegram
│
├── offline_packages\                             ← all project .whl files
│
├── llama_cpu\                                    ← CPU build
├── llama_gpu\                                    ← GPU/CUDA build
│
├── model\
│   └── qwen2.5-7b-instruct-q3_k_m.gguf
│
├── cuda_installer\                               ← GPU only
│   └── cuda_12.2.0_windows.exe
│
└── Healthcare_reporting_system_backup\           ← full project folder
    ├── START.bat                                 ← launches the whole system
    ├── frontend\
    │   ├── node_modules\                        ← must be included!
    │   └── start_frontend.bat
    └── python-service\
        └── start_backend.bat
```

---

---

# PART 2 — Steps on the Offline PC

Plug in your USB drive (or copy files from it), then follow each step in order. No internet is needed from this point forward.

---

## Step 1 — Install Python 3.11.9

Run `python-3.11.9-amd64.exe` from the installers folder.

> **Note:** If another Python version is already installed, that is fine — they can coexist. You can leave "Add to PATH" unchecked; we will target Python 3.11 explicitly using `py -3.11`.

---

## Step 2 — Install Node.js v24.11.0

Run `node-v24.11.0-x64.msi` and follow the installer normally. Check **"Add to PATH"** when prompted.

> **Why is this needed if `node_modules` is already there?**
> `start_frontend.bat` runs `node node_modules\.bin\vite`. Node.js provides the `node.exe` binary that executes this command. Without it installed, the bat file fails with *'node' is not recognized*. The packages in `node_modules` are just files — they cannot run themselves.

---

## Step 3 — Install CUDA Drivers (GPU Only — Skip for CPU)

Run the CUDA installer from your USB. Choose **Express Installation**. After it finishes, **restart the PC** before continuing.

After restart, verify:

```powershell
nvidia-smi
# Should print GPU name and CUDA version

nvcc --version
# Should show: release 12.2 (or whichever version you downloaded)
```

Skip this step entirely if the offline PC is CPU-only.

---

## Step 4 — Copy Project Files

Copy the entire `Healthcare_reporting_system_backup\` folder from USB to `C:\`. The result should look like:

```
C:\Healthcare_reporting_system_backup\
├── START.bat                ← double-click this to launch everything
├── frontend\
│   ├── node_modules\        ← already there from the copy
│   ├── package.json
│   └── start_frontend.bat
└── python-service\
    ├── main.py
    ├── requirements.txt
    ├── .env
    └── start_backend.bat
```

---

## Step 5 — Create Python Virtual Environment

```powershell
cd C:\Healthcare_reporting_system_backup\python-service

# Create a fresh venv targeting Python 3.11 specifically
py -3.11 -m venv venv_offline

# Activate it
venv_offline\Scripts\activate

# Verify the correct version is active
python --version
# Must print: Python 3.11.9

# Install all project packages from USB (no internet)
pip install --no-index --find-links=C:\TransferFolder\offline_packages -r requirements.txt
```

> Adjust the `--find-links` path to wherever you copied the `offline_packages` folder on this PC.

---

## Step 6 — Install llama-cpp-python

First, check whether the offline PC has an NVIDIA GPU:

```powershell
nvidia-smi
# If this prints GPU info → use Option B (GPU)
# If 'nvidia-smi' is not recognized → use Option A (CPU)
```

### Option A — CPU-only

```powershell
pip install --no-index --find-links=C:\TransferFolder\llama_cpu llama-cpp-python
```

### Option B — GPU/CUDA

```powershell
# CUDA drivers must be installed first (Step 3)
pip install --no-index --find-links=C:\TransferFolder\llama_gpu llama-cpp-python
```

**Quick comparison:**

| | CPU-only | NVIDIA GPU |
|---|---|---|
| Works without GPU drivers? | Yes | No — CUDA required |
| Wheel folder | `llama_cpu\` | `llama_gpu\` |
| AI speed | 30–90 sec / paragraph | 2–5 sec / paragraph |
| RAM / VRAM needed | 4–5 GB RAM | 4–5 GB VRAM |
| Model file | Same `.gguf` | Same `.gguf` |

---

## Step 7 — Place the AI Model File

```powershell
mkdir C:\models
copy C:\TransferFolder\model\qwen2.5-7b-instruct-q3_k_m.gguf  C:\models\
```

---

## Step 8 — Configure `.env`

Open `C:\Healthcare_reporting_system_backup\python-service\.env` in Notepad and set:

```env
PORT=8000
ENVIRONMENT=development

# AI Settings
ENABLE_AI=true
QWEN_MODEL_PATH=C:\models\qwen2.5-7b-instruct-q3_k_m.gguf

# To disable AI entirely, change the line above to:
# ENABLE_AI=false
```

> If you set `ENABLE_AI=false`, skip Steps 6 and 7 entirely. The system runs fully without AI.

---

## Step 9 — Configure GPU vs CPU in `ai_service.py`

Open `C:\Healthcare_reporting_system_backup\python-service\app\mortality\ai_service.py` and find the `Llama()` constructor. Set `n_gpu_layers` based on your hardware:

### For GPU:

```python
self.llm = Llama(
    model_path=model_path,
    n_gpu_layers=35,    # 35 for Q3/Q4 models, 41 for Q8
    n_ctx=8192,
    n_batch=512,
    n_threads=8,
    verbose=False
)
```

### For CPU only:

```python
self.llm = Llama(
    model_path=model_path,
    n_gpu_layers=0,     # 0 = CPU only, no GPU used
    n_ctx=8192,
    n_batch=512,
    n_threads=8,        # Set to your CPU core count
    verbose=False
)
```

---

---

# PART 3 — Running the System

The root project folder contains a `START.bat` file that launches both services at once. Just double-click it — no terminal needed.

```
C:\Healthcare_reporting_system_backup\START.bat   ← double-click this
```

`START.bat` opens two windows automatically:
- **Window 1** — Backend (Python/FastAPI) — wait for `Uvicorn running on http://0.0.0.0:8000`
- **Window 2** — Frontend (Vite) — wait for `Local: http://localhost:5173`

Then open your browser at: **http://localhost:5173**

> **Important:** Keep both black windows open while using the system. Closing either one stops that service.

---

### Running Services Individually (if needed)

You can also start each service separately by double-clicking their own bat files:

| File | Location | Wait for... |
|------|----------|-------------|
| `start_backend.bat` | `python-service\` | `Uvicorn running on http://0.0.0.0:8000` |
| `start_frontend.bat` | `frontend\` | `Local: http://localhost:5173` |

Always start the backend first.

---

### Bat File Contents (already in project — no action needed)

**`START.bat`** (root of project):

```bat
@echo off
title Healthcare System — Launcher
echo Starting Healthcare Reporting System...
echo.

echo Launching backend...
start "Healthcare Backend" cmd /k "cd python-service && call venv_offline\Scripts\activate && python main.py"

timeout /t 3 /nobreak >nul

echo Launching frontend...
start "Healthcare Frontend" cmd /k "cd frontend && node node_modules\.bin\vite"

echo.
echo Both services are starting. Open http://localhost:5173 in your browser.
pause
```

**`start_backend.bat`** (inside `python-service\`):

```bat
@echo off
title Healthcare System — Backend
echo Starting backend server...
call venv_offline\Scripts\activate
python main.py
pause
```

**`start_frontend.bat`** (inside `frontend\`):

```bat
@echo off
title Healthcare System — Frontend
echo Starting frontend...
node node_modules\.bin\vite
pause
```

---

---

# PART 4 — Verification & Troubleshooting

## Verification Checklist

```powershell
# Check installed software
python --version          # Python 3.11.9
node --version            # v24.11.0
npm --version             # 10.x or higher

# GPU only
nvidia-smi                # Shows GPU + CUDA version
nvcc --version            # Shows CUDA compiler version
```

```powershell
# Check Python packages
cd C:\Healthcare_reporting_system_backup\python-service
venv_offline\Scripts\activate

python -c "import fastapi, pandas, matplotlib; print('Core packages OK')"
python -c "from llama_cpp import Llama; print('llama-cpp-python OK')"
```

```powershell
# Check model file
dir C:\models\
# Should show: qwen2.5-7b-instruct-q3_k_m.gguf
```

**Service URLs:**

| Service | URL |
|---------|-----|
| Frontend (main app) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Health Check | http://localhost:8000/health |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## Troubleshooting

### 'python is not recognized' or wrong version

```powershell
# Use the py launcher to target 3.11 explicitly:
py -3.11 --version

# If py is not found, Python was not installed correctly.
# Re-run python-3.11.9-amd64.exe and check 'Add to PATH'.
```

---

### Frontend won't start — 'node is not recognized'

Node.js is not in PATH. Re-run `node-v24.11.0-x64.msi` and check **"Add to PATH"**. Then restart PowerShell and try again.

> Even with `node_modules` present, the `node.exe` binary must be installed separately — it is not included inside `node_modules`.

---

### 'CUDA not found' or llama-cpp-python crashes on GPU

```powershell
# Check CUDA environment variable:
echo %CUDA_PATH%
# Should show: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2

# If empty: re-run CUDA installer, then restart PC.

# Reinstall the GPU build:
pip uninstall llama-cpp-python
pip install --no-index --find-links=C:\TransferFolder\llama_gpu llama-cpp-python
```

---

### Model file not found

```powershell
# Verify the file exists:
dir C:\models\*.gguf

# Then check that QWEN_MODEL_PATH in .env matches the exact path shown above.
```

---

### Out of memory during AI generation

```python
# In ai_service.py, reduce context size:
n_ctx=4096    # instead of 8192

# q3_k_m.gguf is already the smallest available model.
# If RAM is still tight, reduce n_ctx further or disable AI:
```

```env
ENABLE_AI=false
```

---

### Backend starts but frontend can't reach the API

```powershell
# Confirm backend is running — open in browser:
# http://localhost:8000/health
# Should return: {"status": "ok"}

# If Windows Firewall is blocking port 8000:
netsh advfirewall firewall add rule name="Healthcare Backend" dir=in action=allow protocol=TCP localport=8000
```

---

*Smart Healthcare Reporting System · v3.0.0 · Offline Installation Guide*
