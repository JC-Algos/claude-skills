#!/usr/bin/env python3
"""
News Research Module - Uses Gemini Deep Research for stock news analysis
Integrates with n8n workflow for Phase 2 (News Analysis)
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Paths
PROMPT_PATH = Path(__file__).parent / "prompts" / "stock_strategist.md"
OUTPUT_DIR = Path("/root/clawd/research/news")

def load_prompt(ticker: str, market: str = "HK") -> str:
    """Load and customize the prompt template"""
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract just the prompt part (skip the header)
    prompt_start = content.find("你係【首席股票策略師")
    if prompt_start == -1:
        prompt_start = 0
    prompt = content[prompt_start:]
    
    # Format ticker based on market
    if market.upper() == "HK":
        formatted_ticker = f"{ticker.zfill(4)}.HK"
    else:
        formatted_ticker = ticker.upper()
    
    # Replace placeholder
    prompt = prompt.replace("[TICKER]", formatted_ticker)
    
    return prompt

def run_gemini_research(prompt: str, ticker: str, market: str) -> dict:
    """Run Gemini CLI for deep research"""
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"{ticker}_{market}_{timestamp}.md"
    
    try:
        # Run gemini CLI with the prompt
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes timeout for deep research
            env={**os.environ, "TERM": "dumb"}
        )
        
        if result.returncode == 0:
            response = result.stdout.strip()
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# {ticker}.{market} 新聞分析報告\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
                f.write("---\n\n")
                f.write(response)
            
            return {
                "success": True,
                "ticker": ticker,
                "market": market,
                "report": response,
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Gemini CLI failed",
                "ticker": ticker,
                "market": market
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Research timeout (>3 minutes)",
            "ticker": ticker,
            "market": market
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Gemini CLI not found. Install with: npm install -g @anthropic/gemini-cli",
            "ticker": ticker,
            "market": market
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker,
            "market": market
        }

def main():
    parser = argparse.ArgumentParser(description="Stock News Research via Gemini")
    parser.add_argument("ticker", help="Stock ticker (e.g., 0700, AAPL)")
    parser.add_argument("--market", "-m", default="HK", help="Market: HK or US")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Load and customize prompt
    prompt = load_prompt(args.ticker, args.market)
    
    # Run research
    result = run_gemini_research(prompt, args.ticker, args.market)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["success"]:
            print(result["report"])
            print(f"\n📁 Saved to: {result['output_file']}")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

# Flask API for n8n integration
def create_app():
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'news-research'})
    
    @app.route('/research', methods=['POST'])
    def research():
        """
        Run news research for a stock
        Body: {"ticker": "0700", "market": "HK"}
        """
        data = request.json or {}
        ticker = data.get('ticker')
        market = data.get('market', 'HK')
        
        if not ticker:
            return jsonify({'error': 'ticker is required'}), 400
        
        prompt = load_prompt(ticker, market)
        result = run_gemini_research(prompt, ticker, market)
        
        return jsonify(result)
    
    @app.route('/research/telegram', methods=['POST'])
    def research_telegram():
        """Research and send to Telegram"""
        data = request.json or {}
        ticker = data.get('ticker')
        market = data.get('market', 'HK')
        chat_id = data.get('chat_id', '1016466977')
        
        if not ticker:
            return jsonify({'error': 'ticker is required'}), 400
        
        prompt = load_prompt(ticker, market)
        result = run_gemini_research(prompt, ticker, market)
        
        if result["success"]:
            # Send via clawdbot CLI
            try:
                send_result = subprocess.run(
                    ['/usr/bin/clawdbot', 'message', 'send',
                     '--channel', 'telegram',
                     '--target', str(chat_id),
                     '--message', result["report"][:4000]],  # Telegram limit
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                result["sent"] = send_result.returncode == 0
            except Exception as e:
                result["sent"] = False
                result["send_error"] = str(e)
        
        return jsonify(result)
    
    return app


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        # Run as API server
        app = create_app()
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5004
        print(f"Starting News Research API on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        main()
