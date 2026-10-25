@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%cd%"
set "BACK=%ROOT%\backend"
set "FRONT=%ROOT%\frontend"
set "PY=%BACK%\venv\Scripts\python.exe"

echo === AI Electricity Analyzer ===

where python >nul 2>&1
if errorlevel 1 ( echo [ERROR] Python was not found. Install Python 3.10+ from python.org and tick "Add to PATH". & goto :fail )
where npm >nul 2>&1
if errorlevel 1 ( echo [ERROR] Node.js/npm was not found. Install Node.js LTS from nodejs.org. & goto :fail )

if not exist "%PY%" (
  echo Creating Python virtual environment...
  python -m venv "%BACK%\venv"
  if errorlevel 1 ( echo [ERROR] Could not create the virtual environment. & goto :fail )
)

if not exist "%BACK%\venv\.deps_installed" (
  echo Installing backend requirements...
  "%PY%" -m pip install -r "%BACK%\requirements.txt"
  if errorlevel 1 ( echo [ERROR] pip install failed. Check your internet connection. & goto :fail )
  echo ok> "%BACK%\venv\.deps_installed"
)

if exist "%BACK%\data\household_power_consumption.txt" goto :havedata
if exist "%BACK%\data\sample_household_power_consumption.txt" goto :havedata

echo Real dataset not found. Trying a one-time download...
pushd "%BACK%"
"%PY%" download_dataset.py
popd
if exist "%BACK%\data\household_power_consumption.txt" goto :havedata

echo.
echo [WARNING] Could not get the real dataset. Creating a SYNTHETIC sample file for demo use.
echo           Results will be marked "Sample data". Add the real file later - see README.md.
echo.
pushd "%BACK%"
"%PY%" generate_sample_data.py
set "GEN_ERR=%errorlevel%"
popd
if not "%GEN_ERR%"=="0" ( echo [ERROR] Could not create sample data. & goto :fail )

:havedata
if not exist "%BACK%\models\linear_regression.joblib" goto :train
if not exist "%BACK%\models\decision_tree.joblib" goto :train
if not exist "%BACK%\models\kmeans.joblib" goto :train
if not exist "%BACK%\outputs\metrics.json" goto :train
rem Real file arrived after a sample-trained run: retrain once on real data.
if exist "%BACK%\data\household_power_consumption.txt" if exist "%BACK%\outputs\trained_on_sample.flag" goto :train
echo Trained models found - skipping training.
goto :trained

:train
echo Training models - this can take a few minutes...
pushd "%BACK%"
"%PY%" train_model.py
set "TRAIN_ERR=%errorlevel%"
popd
if not "%TRAIN_ERR%"=="0" ( echo [ERROR] Training failed. See messages above. & goto :fail )

:trained

if exist "%FRONT%\node_modules" goto :frontdeps_ok
echo Installing frontend packages...
pushd "%FRONT%"
call npm install
if errorlevel 1 ( popd & echo [ERROR] npm install failed. & goto :fail )
popd
:frontdeps_ok

echo Starting backend  on http://127.0.0.1:5000
start "Electricity Analyzer - Backend" /D "%BACK%" cmd /k ""%PY%" app.py"
echo Starting frontend on http://localhost:5173
start "Electricity Analyzer - Frontend" /D "%FRONT%" cmd /k "npm run dev"

timeout /t 6 >nul
start "" http://localhost:5173
echo Both servers are running in their own windows. Close those windows to stop them.
endlocal
exit /b 0

:fail
echo.
echo Setup stopped because of the error above.
pause
endlocal
exit /b 1
