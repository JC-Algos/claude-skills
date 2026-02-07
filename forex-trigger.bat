@echo off
REM ============================================
REM Forex Analyst n8n Webhook Trigger (Windows)
REM ============================================

SET N8N_WEBHOOK=http://localhost:5678/webhook/forex-analysis
SET CURRENCY_PAIR=EURUSD

echo Triggering Forex Analysis for %CURRENCY_PAIR%...

curl -X POST "%N8N_WEBHOOK%?currency_pair=%CURRENCY_PAIR%"

echo.
echo Done! Check your email for the report.
pause
