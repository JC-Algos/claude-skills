@echo off
REM ============================================
REM Forex Analyst n8n Webhook Trigger (Windows)
REM ============================================
REM
REM This BAT file triggers the Forex Analyst workflow in n8n
REM You can modify the CURRENCY_PAIR variable below
REM
REM Supported pairs: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCAD
REM ============================================

echo.
echo ============================================
echo    FOREX ANALYST WORKFLOW TRIGGER
echo ============================================
echo.

REM ====== CONFIGURATION ======
SET N8N_WEBHOOK_URL=http://localhost:5678/webhook/forex-analysis
SET CURRENCY_PAIR=EURUSD

REM ===========================

echo [INFO] Target: %N8N_WEBHOOK_URL%
echo [INFO] Currency Pair: %CURRENCY_PAIR%
echo.
echo [STEP 1] Triggering n8n workflow...
echo.

REM Trigger the webhook with currency_pair parameter
curl -X POST "%N8N_WEBHOOK_URL%?currency_pair=%CURRENCY_PAIR%"

echo.
echo.
echo ============================================
echo [SUCCESS] Workflow triggered!
echo ============================================
echo.
echo Check your email inbox for the analysis report.
echo (Processing time: 2-5 minutes depending on news volume)
echo.
pause
