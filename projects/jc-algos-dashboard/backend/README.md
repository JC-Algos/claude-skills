# JC Algos Dashboard Backend API

Flask API serving HSI forecasts and market intelligence data for the JC Algos dashboard.

## Endpoints

| Endpoint | Description | Cache |
|----------|-------------|-------|
| `GET /api/health` | Health check | - |
| `GET /api/forecast/latest` | Latest HSI forecast | - |
| `GET /api/forecast/history` | Last 30 forecasts (deduped by date) | - |
| `GET /api/forecast/accuracy` | Predicted vs actual comparison | 1 hour |
| `GET /api/market/hk` | HK market squeeze/RRG analysis | 30 min |
| `GET /api/market/us` | US market squeeze/RRG analysis | 30 min |
| `POST /api/cache/clear` | Clear all cached data (requires X-Admin-Key header) | - |

## Response Examples

### /api/forecast/latest
```json
{
  "date": "2026-02-07",
  "direction": "DOWN",
  "high": 27383,
  "low": 26821,
  "confidence": 0.5,
  "judges": [
    {"name": "xgb+catboost", "direction": "DOWN", "probability": 0.403},
    {"name": "GRU", "direction": "UP", "probability": 0.681},
    {"name": "ARIMA", "direction": "UP", "probability": 0.509},
    {"name": "Diffusion", "direction": "NEUTRAL", "score": 0}
  ],
  "bullish_factors": ["FXI+2.7%", "SPX+2.0%"],
  "bearish_factors": ["<EMA20", "<MA5"]
}
```

### /api/forecast/accuracy
```json
{
  "range_accuracy": 75.0,
  "direction_accuracy": 50.0,
  "total_compared": 4,
  "details": [...]
}
```

## Deployment

Running on Docker as part of the n8n compose stack:
- URL: https://dashboard.srv1295571.hstgr.cloud
- Port: 5020
- CORS: Allows jc-algos.com

### Docker Compose Entry
The service is defined in `/docker/n8n/docker-compose.yml` as `dashboard-api`.

### Required Volumes
- `/root/clawd/projects/jc-algos-dashboard/backend:/app:ro` — API code
- `/root/clawd:/clawd:ro` — Read-only access to predictions.jsonl and scripts

## Local Development

```bash
cd /root/clawd/projects/jc-algos-dashboard/backend
pip install -r requirements.txt
python3 app.py
```

Server runs on http://localhost:5020

## Files

- `app.py` — Main Flask application
- `run_analyzer.py` — Wrapper script for running market analyzer scripts (handles Docker path differences)
- `requirements.txt` — Python dependencies
- `Dockerfile` — Standalone Docker build (alternative to compose)
- `docker-compose-snippet.yml` — Copy-paste snippet for docker-compose.yml
