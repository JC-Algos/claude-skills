#!/usr/bin/env python3
"""
Daily Valid Signals Report
Fetches today's valid signals from the signal page backend and formats for Telegram.
Runs Mon-Fri at 4:45 PM HKT.
"""

import requests
import sys
from datetime import datetime
import pytz

# Configuration
API_BASE = "https://signal.srv1295571.hstgr.cloud"
HK_TZ = pytz.timezone('Asia/Hong_Kong')
EXCHANGES = ["HKEX"]  # Start with HKEX, can add BATS later

def fetch_valid_signals(exchange, days_ago=1):
    """Fetch valid signals from backend API"""
    try:
        resp = requests.post(
            f"{API_BASE}/api/signals/fetch",
            json={"exchange": exchange, "days_ago": days_ago},
            timeout=120
        )
        data = resp.json()
        signals = data.get("signals", [])
        return [s for s in signals if s.get("valid_signal") == "Yes"]
    except Exception as e:
        print(f"Error fetching {exchange}: {e}", file=sys.stderr)
        return []


def format_ticker(ticker_symbol):
    """Clean ticker for display: HKG:2400 → 2400"""
    if ":" in ticker_symbol:
        return ticker_symbol.split(":")[1]
    return ticker_symbol


def format_pl(pl_str):
    """Format P/L percentage"""
    if not pl_str:
        return "0.00%"
    try:
        val = float(pl_str)
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.2f}%"
    except:
        return pl_str


def format_report(all_signals, now_hk):
    """Format the Telegram message"""
    date_str = now_hk.strftime("%Y-%m-%d %H:%M HKT")
    
    lines = []
    lines.append("📊 **JC Algos 每日有效信號**")
    lines.append(f"📅 {date_str}")
    lines.append("")
    
    for exchange, signals in all_signals.items():
        if not signals:
            lines.append(f"📭 {exchange}: 今日無有效信號")
            lines.append("")
            continue
        
        bull = [s for s in signals if s.get("sentiment") == "好"]
        bear = [s for s in signals if s.get("sentiment") == "淡"]
        
        total = len(signals)
        lines.append(f"🏦 **{exchange}** — {total} 個有效信號 ({len(bull)} 好 / {len(bear)} 淡)")
        lines.append("")
        
        if bull:
            lines.append("🟢 **看好信號**")
            lines.append("")
            for s in sorted(bull, key=lambda x: float(x.get('pl_percent', 0) or 0), reverse=True):
                ticker = format_ticker(s['ticker_symbol'])
                strategy = s.get('strategy', '')
                trigger = s.get('trigger_price', '-')
                close = s.get('present_close', '-')
                pl = format_pl(s.get('pl_percent'))
                lines.append(f"• **{ticker}** | {strategy}")
                lines.append(f"  觸發價: {trigger} → 收市價: {close} | P/L: {pl}")
            lines.append("")
        
        if bear:
            lines.append("🔴 **看淡信號**")
            lines.append("")
            for s in sorted(bear, key=lambda x: float(x.get('pl_percent', 0) or 0), reverse=True):
                ticker = format_ticker(s['ticker_symbol'])
                strategy = s.get('strategy', '')
                trigger = s.get('trigger_price', '-')
                close = s.get('present_close', '-')
                pl = format_pl(s.get('pl_percent'))
                lines.append(f"• **{ticker}** | {strategy}")
                lines.append(f"  觸發價: {trigger} → 收市價: {close} | P/L: {pl}")
            lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("🐷 Oracle | JC Algos Signal Report")
    
    return "\n".join(lines)


def main():
    now_hk = datetime.now(HK_TZ)
    
    # Accept exchange argument: HKEX (default) or BATS
    exchanges = EXCHANGES
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg in ("BATS", "US"):
            exchanges = ["BATS"]
        elif arg == "HKEX":
            exchanges = ["HKEX"]
        elif arg == "ALL":
            exchanges = ["HKEX", "BATS"]
        else:
            exchanges = [arg]
    
    all_signals = {}
    for exchange in exchanges:
        valid = fetch_valid_signals(exchange)
        all_signals[exchange] = valid
        print(f"{exchange}: {len(valid)} valid signals", file=sys.stderr)
    
    report = format_report(all_signals, now_hk)
    print(report)


if __name__ == "__main__":
    main()
