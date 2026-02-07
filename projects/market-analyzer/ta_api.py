#!/usr/bin/env python3
"""
Technical Analysis API for JC-Algos Website
Combines TA report, Technical Chart, and RRG Chart
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ta_analyzer import MarketAnalyzer, NumpyEncoder
from rrg_rs_analyzer import generate_rrg_chart, get_rs_ranking, get_rrg_quadrant_zh
from generate_chart import generate_chart
from generate_interactive_chart import generate_interactive_chart

app = Flask(__name__)
app.json.encoder = NumpyEncoder
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize analyzer
analyzer = MarketAnalyzer()

# Chart output directory (in Docker, uses /app/charts via CHART_DIR env var)
CHART_DIR = os.environ.get('CHART_DIR', '/root/clawd/research/charts')
# Fallback: Use /app/charts if running in Docker and env var not set
if not os.environ.get('CHART_DIR') and os.path.exists('/app'):
    CHART_DIR = '/app/charts'
os.makedirs(CHART_DIR, exist_ok=True)
print(f"📁 Using chart directory: {CHART_DIR}")


@app.route('/api/ta/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'technical-analysis-api',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/ta/analyze', methods=['GET', 'POST'])
def analyze():
    """
    Full technical analysis endpoint
    
    GET: /api/ta/analyze?ticker=0700&market=HK
    POST: {"ticker": "0700", "market": "HK"}
    
    Returns:
        - TA report (formatted text)
        - Technical chart URL
        - RRG chart URL
        - Raw analysis data
    """
    if request.method == 'POST':
        data = request.json or {}
    else:
        data = request.args.to_dict()
    
    ticker = data.get('ticker', '').upper().strip()
    market = data.get('market', 'HK').upper().strip()
    
    if not ticker:
        return jsonify({'success': False, 'error': 'ticker is required'}), 400
    
    # Validate market
    if market not in ['HK', 'US']:
        return jsonify({'success': False, 'error': 'market must be HK or US'}), 400
    
    result = {
        'success': False,
        'ticker': ticker,
        'market': market,
        'report': '',
        'charts': {
            'technical': None,
            'interactive': None,
            'rrg': None
        },
        'data': None,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # 1. Run full TA analysis
        analysis = analyzer.full_analysis(ticker, market)
        if not analysis.get('success'):
            return jsonify({
                'success': False,
                'error': analysis.get('error', 'Analysis failed'),
                'ticker': ticker,
                'market': market
            }), 400
        
        # 2. Generate formatted report
        result['report'] = analyzer.generate_report_zh(analysis)
        result['data'] = {
            'name': analysis.get('name'),
            'price': analysis.get('price'),
            'ema': analysis.get('ema'),
            'dmi_adx': analysis.get('dmi_adx'),
            'fibonacci': analysis.get('fibonacci'),
            'volume': analysis.get('volume'),
            'volume_profile': analysis.get('volume_profile'),
            'candlestick': analysis.get('candlestick')
        }
        
        # 3. Generate technical chart (static PNG)
        try:
            os.makedirs(CHART_DIR, exist_ok=True)
            chart_path = generate_chart(ticker, market, period='13mo', output_dir=CHART_DIR)
            if chart_path and os.path.exists(chart_path):
                chart_filename = os.path.basename(chart_path)
                result['charts']['technical'] = f'/api/ta/chart/{chart_filename}'
        except Exception as e:
            result['charts']['technical_error'] = str(e)
        
        # 3b. Generate interactive chart (Plotly HTML with CDN)
        try:
            interactive_path = generate_interactive_chart(ticker, market, output_dir=CHART_DIR, use_cdn=True)
            if interactive_path and os.path.exists(interactive_path):
                interactive_filename = os.path.basename(interactive_path)
                result['charts']['interactive'] = f'/api/ta/chart/{interactive_filename}'
        except Exception as e:
            result['charts']['interactive_error'] = str(e)
        
        # 4. Generate RRG chart
        try:
            # Ensure output directory exists
            os.makedirs(CHART_DIR, exist_ok=True)
            rrg_filename = f'rrg_{ticker}_{market}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            rrg_path = os.path.join(CHART_DIR, rrg_filename)
            # Make sure rrg_path is absolute and directory exists
            rrg_path = os.path.abspath(rrg_path)
            os.makedirs(os.path.dirname(rrg_path), exist_ok=True)
            rrg_data = generate_rrg_chart(ticker, market, output_path=rrg_path)
            
            if rrg_data.get('success') and os.path.exists(rrg_path):
                result['charts']['rrg'] = f'/api/ta/chart/{rrg_filename}'
                result['data']['rrg'] = {
                    'rs_ratio': rrg_data.get('rs_ratio'),
                    'rs_momentum': rrg_data.get('rs_momentum'),
                    'quadrant': rrg_data.get('quadrant'),
                    'quadrant_zh': get_rrg_quadrant_zh(rrg_data.get('quadrant', ''))
                }
        except Exception as e:
            result['charts']['rrg_error'] = str(e)
        
        # 5. Get RS ranking
        try:
            rs_data = get_rs_ranking(ticker, market)
            if rs_data.get('success'):
                result['data']['rs_ranking'] = {
                    'current_rank': rs_data['rankings']['current']['rank'],
                    'total_stocks': rs_data['rankings']['current']['total_stocks'],
                    'score': rs_data['rankings']['current']['score'],
                    'rank_changes': rs_data.get('rank_changes', {})
                }
        except Exception as e:
            result['data']['rs_ranking_error'] = str(e)
        
        result['success'] = True
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'ticker': ticker,
            'market': market
        }), 500


@app.route('/api/ta/chart/<filename>')
def serve_chart(filename):
    """Serve chart images (PNG or HTML)"""
    chart_path = os.path.join(CHART_DIR, filename)
    if os.path.exists(chart_path):
        if filename.endswith('.html'):
            return send_file(chart_path, mimetype='text/html')
        return send_file(chart_path, mimetype='image/png')
    return jsonify({'error': 'Chart not found'}), 404


@app.route('/api/ta/interactive', methods=['GET', 'POST'])
def interactive_chart_endpoint():
    """
    Generate interactive Plotly chart (CDN version ~40KB)
    
    GET: /api/ta/interactive?ticker=0700&market=HK
    POST: {"ticker": "0700", "market": "HK"}
    
    Returns:
        - Interactive chart URL
        - File size info
    """
    if request.method == 'POST':
        data = request.json or {}
    else:
        data = request.args.to_dict()
    
    ticker = data.get('ticker', '').upper().strip()
    market = data.get('market', 'HK').upper().strip()
    
    if not ticker:
        return jsonify({'success': False, 'error': 'ticker is required'}), 400
    
    if market not in ['HK', 'US']:
        return jsonify({'success': False, 'error': 'market must be HK or US'}), 400
    
    try:
        os.makedirs(CHART_DIR, exist_ok=True)
        chart_path = generate_interactive_chart(ticker, market, output_dir=CHART_DIR, use_cdn=True)
        
        if chart_path and os.path.exists(chart_path):
            chart_filename = os.path.basename(chart_path)
            file_size = os.path.getsize(chart_path)
            
            return jsonify({
                'success': True,
                'ticker': ticker,
                'market': market,
                'chart_url': f'/api/ta/chart/{chart_filename}',
                'file_size_kb': round(file_size / 1024, 1),
                'type': 'interactive',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate chart',
                'ticker': ticker,
                'market': market
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'ticker': ticker,
            'market': market
        }), 500


@app.route('/api/ta/quick', methods=['GET'])
def quick_analysis():
    """
    Quick analysis - returns just the key metrics without charts
    Faster for list views
    """
    ticker = request.args.get('ticker', '').upper().strip()
    market = request.args.get('market', 'HK').upper().strip()
    
    if not ticker:
        return jsonify({'success': False, 'error': 'ticker is required'}), 400
    
    try:
        analysis = analyzer.full_analysis(ticker, market)
        if not analysis.get('success'):
            return jsonify({
                'success': False,
                'error': analysis.get('error', 'Analysis failed')
            }), 400
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'market': market,
            'name': analysis.get('name'),
            'price': analysis.get('price'),
            'trend': analysis.get('ema', {}).get('trend_zh'),
            'adx': analysis.get('dmi_adx', {}).get('ADX'),
            'volume_ratio': analysis.get('volume', {}).get('ratio'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ta/batch', methods=['POST'])
def batch_analysis():
    """
    Batch analysis for multiple tickers
    POST: {"tickers": ["0700", "9988"], "market": "HK"}
    """
    data = request.json or {}
    tickers = data.get('tickers', [])
    market = data.get('market', 'HK').upper()
    
    if not tickers:
        return jsonify({'success': False, 'error': 'tickers array is required'}), 400
    
    results = []
    for ticker in tickers[:10]:  # Limit to 10 tickers
        try:
            analysis = analyzer.full_analysis(ticker, market)
            results.append({
                'ticker': ticker,
                'success': analysis.get('success', False),
                'name': analysis.get('name'),
                'price': analysis.get('price'),
                'trend': analysis.get('ema', {}).get('trend_zh') if analysis.get('success') else None,
                'error': analysis.get('error') if not analysis.get('success') else None
            })
        except Exception as e:
            results.append({
                'ticker': ticker,
                'success': False,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'count': len(results),
        'results': results
    })


@app.route('/api/southbound/history', methods=['GET'])
def southbound_history():
    """
    Fetch historical Southbound (港股通) data from East Money API
    GET: /api/southbound/history?days=100
    
    Returns: Daily net inflow data with 10-day MA
    """
    import requests
    from datetime import datetime, timedelta
    
    days = int(request.args.get('days', 100))
    days = min(days, 365)  # Cap at 1 year
    
    try:
        base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://data.eastmoney.com/hsgt/index.html"
        }
        
        all_data = {}
        
        # Fetch both Shanghai and Shenzhen southbound
        for mutual_type in ["002", "004"]:  # 002=SH, 004=SZ
            params = {
                "reportName": "RPT_MUTUAL_DEAL_HISTORY",
                "columns": "ALL",
                "filter": f'(MUTUAL_TYPE="{mutual_type}")',
                "pageNumber": 1,
                "pageSize": days + 20,  # Extra buffer for MA calculation
                "sortColumns": "TRADE_DATE",
                "sortTypes": "-1"
            }
            
            resp = requests.get(base_url, params=params, headers=headers, timeout=15)
            data = resp.json()
            
            if data.get("result") and data["result"].get("data"):
                for rec in data["result"]["data"]:
                    date_str = rec.get("TRADE_DATE", "")[:10]
                    net_amt = rec.get("NET_DEAL_AMT", 0) or 0
                    
                    if date_str not in all_data:
                        all_data[date_str] = {"sh_net": 0, "sz_net": 0}
                    
                    if mutual_type == "002":
                        all_data[date_str]["sh_net"] = net_amt
                    else:
                        all_data[date_str]["sz_net"] = net_amt
        
        # Convert to sorted list (oldest first for proper EMA calculation)
        sorted_dates = sorted(all_data.keys())  # Oldest first
        result = []
        net_values = []
        
        # EMA multipliers
        ema10, ema21, ema60 = None, None, None
        k10 = 2 / (10 + 1)
        k21 = 2 / (21 + 1)
        k60 = 2 / (60 + 1)
        
        for i, date_str in enumerate(sorted_dates):
            row = all_data[date_str]
            total_net = row["sh_net"] + row["sz_net"]
            net_values.append(total_net)
            
            # Calculate EMAs
            if i == 0:
                ema10 = total_net
                ema21 = total_net
                ema60 = total_net
            else:
                ema10 = total_net * k10 + ema10 * (1 - k10)
                ema21 = total_net * k21 + ema21 * (1 - k21)
                ema60 = total_net * k60 + ema60 * (1 - k60)
            
            result.append({
                "date": date_str,
                "sh_net": row["sh_net"],
                "sz_net": row["sz_net"],
                "total_net": total_net,
                "ema10": round(ema10, 2) if i >= 9 else None,
                "ema21": round(ema21, 2) if i >= 20 else None,
                "ema60": round(ema60, 2) if i >= 59 else None
            })
        
        # Return only the most recent N days (result is already oldest first)
        result = result[-days:]
        
        return jsonify({
            "success": True,
            "count": len(result),
            "unit": "million_cny",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/hsi/forecast', methods=['GET'])
def hsi_forecast():
    """
    HSI Daily Forecast endpoint
    GET: Returns today's HSI forecast with diffusion-based confidence
    Optional: ?format=telegram for formatted message
    """
    try:
        # Import HSI predict function (mounted at /hsi-forecast in Docker)
        hsi_paths = ['/hsi-forecast/src', '/root/clawd/projects/hsi-forecast/src']
        for hsi_path in hsi_paths:
            if os.path.exists(hsi_path) and hsi_path not in sys.path:
                sys.path.insert(0, hsi_path)
                break
        
        from predict import predict_today, format_telegram
        
        result = predict_today()
        
        # If format=telegram, return formatted message
        fmt = request.args.get('format', 'json')
        if fmt == 'telegram':
            message = format_telegram(result)
            return jsonify({'message': message, **result})
        
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Technical Analysis API')
    parser.add_argument('--port', '-p', type=int, default=5003, help='Port to run on')
    parser.add_argument('--host', '-H', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Technical Analysis API on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
