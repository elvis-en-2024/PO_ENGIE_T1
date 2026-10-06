@echo off
REM Script per eseguire l'aggiornamento quotidiano delle offerte in automatico
REM Configura questo file in "Operazioni Pianificate" di Windows per girare ogni giorno alle 08:00

cd /d "%~dp0\.."

REM Esegue lo script usando python
python -m scripts.update_daily

echo Aggiornamento completato!
