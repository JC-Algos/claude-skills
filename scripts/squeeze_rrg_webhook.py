#!/usr/bin/env python3
"""
Simple Flask webhook for BB Squeeze + RRG analysis
Run: python3 squeeze_rrg_webhook.py
Endpoint: POST /webhook/squeeze-rrg?timeframe=1h
"""

from flask import Flask, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

@app.route('/webhook/squeeze-rrg', methods=['GET', 'POST'])
def squeeze_rrg():
    """Run squeeze + RRG analysis"""
    timeframe = request.args.get('timeframe', '1h')
    output = request.args.get('output', 'telegram')  # telegram sends to channels
    
    try:
        result = subprocess.run(
            ['python3', '/root/clawd/scripts/squeeze_rrg_analyzer.py', timeframe, output],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ}
        )
        
        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'output': result.stdout,
            'errors': result.stderr if result.stderr else None
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010)
