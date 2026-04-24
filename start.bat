@echo off
echo Iniciando API (Backend)...
start cmd /k ".\venv\Scripts\activate && uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

echo Iniciando Streamlit (Frontend)...
start cmd /k ".\venv\Scripts\activate && streamlit run app.py"

echo Servicos iniciados em novas janelas!
