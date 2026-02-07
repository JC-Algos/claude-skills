#!/usr/bin/env python3
"""
Message Relay API - allows n8n (Docker) to send messages via host tools
Runs on host, accessible to Docker via 172.18.0.1
"""
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Simple auth token
AUTH_TOKEN = os.environ.get('RELAY_TOKEN', 'hknews2026')

@app.before_request
def check_auth():
    token = request.headers.get('X-Auth-Token') or request.args.get('token')
    if token != AUTH_TOKEN:
        return jsonify({'error': 'unauthorized'}), 401

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/telegram', methods=['POST'])
def send_telegram():
    """Send message to Telegram via clawdbot"""
    data = request.json or {}
    message = data.get('message', '')
    chat_id = data.get('chat_id', '')
    
    if not message:
        return jsonify({'error': 'message required'}), 400
    
    try:
        # Use clawdbot session send
        cmd = f"/usr/bin/clawdbot session send '{message}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return jsonify({'ok': True, 'stdout': result.stdout, 'stderr': result.stderr})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/whatsapp', methods=['POST'])
def send_whatsapp():
    """Send message to WhatsApp via wacli"""
    data = request.json or {}
    message = data.get('message', '')
    to = data.get('to', '')  # JID
    
    if not message or not to:
        return jsonify({'error': 'message and to required'}), 400
    
    try:
        # Escape single quotes in message
        escaped = message.replace("'", "'\\''")
        cmd = f"wacli send text --to '{to}' --message '{escaped}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify({'ok': True, 'output': result.stdout})
        else:
            return jsonify({'ok': False, 'error': result.stderr or result.stdout}), 500
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/broadcast', methods=['POST'])
def broadcast():
    """Send to multiple destinations - sends Telegram message that Oracle will see"""
    import threading
    
    data = request.json or {}
    message = data.get('message', '')
    telegram = data.get('telegram', False)
    whatsapp_groups = data.get('whatsapp_groups', [])
    
    results = {}
    
    if telegram:
        # Detect news type from message content
        is_us_news = '[US_NEWS_BROADCAST]' in message
        
        if is_us_news:
            msg_file = '/tmp/us_news_trigger.txt'
            trigger_tag = '[US_NEWS_BROADCAST]'
        else:
            msg_file = '/tmp/hk_news_trigger.txt'
            trigger_tag = '[HK_NEWS_TRIGGER]'
        
        # Write full message to temp file
        with open(msg_file, 'w') as f:
            f.write(message)
        
        def send_telegram():
            """Send trigger message to Jason's Telegram via clawdbot message send"""
            try:
                # Send a short trigger - Oracle will read the full file
                trigger = f"{trigger_tag} New headlines ready at {msg_file} - please process and broadcast."
                cmd = [
                    '/usr/bin/clawdbot', 'message', 'send',
                    '--channel', 'telegram',
                    '--target', '1016466977',
                    '--message', trigger
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                with open('/tmp/relay_debug.log', 'a') as f:
                    f.write(f"Send result: {result.returncode} - {result.stdout} {result.stderr}\n")
            except Exception as e:
                with open('/tmp/relay_errors.log', 'a') as f:
                    f.write(f"Telegram send error: {e}\n")
        
        # Run in background
        thread = threading.Thread(target=send_telegram, daemon=True)
        thread.start()
        results['telegram'] = 'triggered'
    
    for jid in whatsapp_groups:
        try:
            escaped = message.replace("'", "'\\''")
            cmd = f"wacli send text --to '{jid}' --message '{escaped}'"
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            results[jid] = 'ok'
        except Exception as e:
            results[jid] = f'error: {e}'
    
    return jsonify({'ok': True, 'results': results})

@app.route('/ai-summary', methods=['POST'])
def ai_summary():
    """Trigger Oracle to generate AI summary via clawdbot session"""
    data = request.json or {}
    headlines = data.get('headlines', '')
    count = data.get('count', 0)
    china_count = data.get('chinaCount', 0)
    
    if not headlines:
        return jsonify({'error': 'headlines required'}), 400
    
    import re
    from datetime import datetime
    import pytz
    
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    now = datetime.now(hk_tz)
    time_str = now.strftime('%m月%d日 %p%I點').replace('AM', '上午').replace('PM', '下午')
    
    # Save headlines to a temp file that Oracle can read
    headlines_file = '/tmp/hk_news_headlines.txt'
    with open(headlines_file, 'w') as f:
        f.write(headlines)
    
    # Trigger Oracle to process and broadcast
    trigger_msg = f"[HK_NEWS_TRIGGER] Please process /tmp/hk_news_headlines.txt and broadcast the Chinese summary to WhatsApp groups. Time: {time_str}"
    
    try:
        cmd = f"/usr/bin/clawdbot session send '{trigger_msg}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return jsonify({'ok': True, 'triggered': True, 'time': time_str})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=False)
