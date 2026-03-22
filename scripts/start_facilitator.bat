@echo off
REM Activate virtualenv if present
if exist .venv\Scripts\activate (
  call .venv\Scripts\activate
)

echo Installing requirements...
pip install -r requirements.txt

set STREAMLIT_SERVER_HEADLESS=true
if "%PORT%"=="" (
  set PORT=8501
)
echo Starting Streamlit on port %PORT%...
streamlit run apps\facilitator_ui.py --server.port %PORT% --server.address 0.0.0.0
