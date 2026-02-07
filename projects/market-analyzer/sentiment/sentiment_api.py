#!/usr/bin/env python3
"""Simple Flask API to serve sentiment analysis JSON data for n8n workflow"""

from flask import Flask, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

REPORTS_DIR = "/root/clawd/projects/market-analyzer/sentiment/reports"

@app.route('/sentiment-data', methods=['GET'])
def get_sentiment_data():
    """Return the latest sentiment analysis JSON"""
    json_path = os.path.join(REPORTS_DIR, "sentiment_analysis_detailed.json")
    
    if not os.path.exists(json_path):
        return jsonify({"error": "No sentiment data available. Run analysis first."}), 404
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "sentiment-api"})

@app.route('/report', methods=['GET'])
def get_report():
    """Return the text report"""
    report_path = os.path.join(REPORTS_DIR, "market_sentiment_report.txt")
    
    if not os.path.exists(report_path):
        return "No report available. Run analysis first.", 404
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    print("Starting Sentiment API server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)
