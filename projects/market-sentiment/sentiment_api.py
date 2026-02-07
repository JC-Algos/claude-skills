#!/usr/bin/env python3
# Sentiment Analysis Data API
from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

# Path where sentiment_analysis_detailed.json is stored
DATA_FILE = '/root/clawd/projects/market-analyzer/sentiment/reports/sentiment_analysis_detailed.json'

@app.route('/sentiment-data')
def get_sentiment_data():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({'error': 'Sentiment data file not found'}), 404
        
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'data_file_exists': os.path.exists(DATA_FILE)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
