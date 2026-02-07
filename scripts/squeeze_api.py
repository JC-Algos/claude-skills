#!/usr/bin/env python3
"""
Squeeze + RRG Analysis API
Port: 5004
Endpoints:
  GET /squeeze-rrg?timeframe=1h&market=US  - Run analysis, return JSON
  GET /health - Health check
"""

from flask import Flask, jsonify, request
import subprocess
import json
import os

app = Flask(__name__)

SCRIPT_DIR = "/root/clawd/scripts"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "squeeze-rrg-api"})

@app.route('/squeeze-rrg')
def squeeze_rrg():
    timeframe = request.args.get('timeframe', '1h')
    market = request.args.get('market', 'US').upper()
    
    # Validate timeframe
    if timeframe not in ['1h', '4h', '1d']:
        return jsonify({"error": "Invalid timeframe. Use: 1h, 4h, 1d"}), 400
    
    # Select script based on market
    if market == 'HK':
        script = os.path.join(SCRIPT_DIR, "hk_squeeze_rrg_analyzer.py")
    else:
        script = os.path.join(SCRIPT_DIR, "squeeze_rrg_analyzer.py")
    
    if not os.path.exists(script):
        return jsonify({"error": f"Script not found: {script}"}), 500
    
    try:
        # Run with 'json' output mode
        result = subprocess.run(
            ["python3", script, timeframe, "json"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            return jsonify({
                "error": "Script execution failed",
                "stderr": result.stderr
            }), 500
        
        # Parse JSON output
        try:
            data = json.loads(result.stdout)
            return jsonify(data)
        except json.JSONDecodeError:
            # If not JSON, return raw text
            return jsonify({
                "raw_output": result.stdout,
                "timeframe": timeframe,
                "market": market
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script timeout (5 min)"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
