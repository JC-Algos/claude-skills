"""
JC Algos Dashboard API v2 — Simple MD file server
Oracle writes forecast.md + market-report.md daily,
frontend fetches and renders them.
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, origins=[
    "https://jc-algos.com",
    "https://www.jc-algos.com",
    "http://localhost:*",
    "http://127.0.0.1:*"
])

DATA_DIR = Path(__file__).parent.parent / "data"

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "jc-algos-dashboard-api",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/api/daily")
def get_daily():
    """Return the combined daily report (forecast + market report)"""
    md_path = DATA_DIR / "daily-report.md"
    if not md_path.exists():
        return jsonify({"error": "No forecast available", "content": ""}), 404
    content = md_path.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
    return jsonify({
        "content": content,
        "updated_at": mtime,
        "filename": "forecast.md"
    })

@app.route("/api/market-report")
def get_market_report():
    """Return market-report.md content"""
    md_path = DATA_DIR / "market-report.md"
    if not md_path.exists():
        return jsonify({"error": "No market report available", "content": ""}), 404
    content = md_path.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
    return jsonify({
        "content": content,
        "updated_at": mtime,
        "filename": "market-report.md"
    })

@app.route("/api/reports")
def list_reports():
    """List all available MD reports with metadata"""
    reports = []
    if DATA_DIR.exists():
        for f in sorted(DATA_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            reports.append({
                "filename": f.name,
                "updated_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "size": f.stat().st_size,
                "endpoint": f"/api/{f.stem}"
            })
    return jsonify({"reports": reports})

# Generic endpoint for any MD file in data/
@app.route("/api/report/<name>")
def get_report(name):
    """Fetch any MD file by name (without .md extension)"""
    safe_name = name.replace("..", "").replace("/", "")
    md_path = DATA_DIR / f"{safe_name}.md"
    if not md_path.exists():
        return jsonify({"error": f"Report '{name}' not found", "content": ""}), 404
    content = md_path.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
    return jsonify({
        "content": content,
        "updated_at": mtime,
        "filename": f"{safe_name}.md"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5020))
    print(f"JC Algos Dashboard API v2 — MD Server on port {port}")
    print(f"Data dir: {DATA_DIR}")
    app.run(host="0.0.0.0", port=port)
