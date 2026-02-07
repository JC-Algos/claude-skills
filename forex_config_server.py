#!/usr/bin/env python3
"""Simple config server for forex pair - runs on port 5010"""
from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)
CONFIG_FILE = '/root/clawd/config/forex_pair.json'

def read_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {"pair": "XAUUSD"}

def write_config(data):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/forex-pair', methods=['GET'])
def get_pair():
    config = read_config()
    return jsonify(config)

@app.route('/forex-pair', methods=['POST'])
def set_pair():
    data = request.get_json() or {}
    pair = data.get('pair', request.args.get('pair', '')).upper().replace('/', '')
    if pair:
        write_config({"pair": pair})
        return jsonify({"status": "ok", "pair": pair})
    return jsonify({"error": "No pair specified"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010)
