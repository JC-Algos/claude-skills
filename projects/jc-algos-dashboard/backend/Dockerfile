FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create cache directory
RUN mkdir -p /tmp/dashboard-cache

# Environment variables
ENV PORT=5020
ENV PREDICTIONS_FILE=/clawd/projects/hsi-forecast/data/predictions.jsonl
ENV HK_ANALYZER_SCRIPT=/clawd/scripts/hk_squeeze_rrg_analyzer.py
ENV US_ANALYZER_SCRIPT=/clawd/scripts/squeeze_rrg_analyzer.py
ENV CACHE_DIR=/tmp/dashboard-cache

EXPOSE 5020

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5020", "--workers", "2", "--timeout", "120", "app:app"]
