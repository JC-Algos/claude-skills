@echo off
REM ============================================
REM Simple Forex Analyst Trigger (No Parameters)
REM ============================================
REM Use this when the currency pair is hardcoded in n8n workflow
REM ============================================

echo.
echo Triggering Forex Analyst Workflow...
echo.

curl -X POST "http://localhost:5678/webhook/forex-analysis"

echo.
echo Done! Check your email.
pause
