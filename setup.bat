@echo off
echo Inizializzazione Ambiente di Scraping PO_scraping_2026...
echo.

echo 1. Creazione ambiente virtuale (venv)...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo [ERRORE] Creazione venv fallita. Assicurati che Python sia installato.
    pause
    exit /b %ERRORLEVEL%
)

echo 2. Attivazione venv e installazione dipendenze...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERRORE] Installazione librerie fallita.
    pause
    exit /b %ERRORLEVEL%
)

echo 3. Installazione browser Chromium per Playwright...
set NODE_TLS_REJECT_UNAUTHORIZED=0
playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo [ATTENZIONE] Installazione Playwright Chromium ha generato un errore. Potrebbe essere necessario configurare i proxy aziendali.
)

echo.
echo ===================================================
echo SETUP COMPLETATO CON SUCCESSO!
echo ===================================================
echo Per avviare il crawler, esegui i seguenti comandi:
echo 1. call venv\Scripts\activate
echo 2. python scripts\crawler_ctes.py
echo ===================================================
pause
