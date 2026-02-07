#!/usr/bin/env python3
"""
HK BB Squeeze + RRG Quadrant Analyzer
Combines BB Squeeze detection with RRG relative strength analysis for HK stocks

Usage:
    python3 hk_squeeze_rrg_analyzer.py [timeframe] [output]
    
    timeframe: 1h, 4h, 1d (default: 1h)
    output: json, telegram, text (default: text)
    
Example:
    python3 hk_squeeze_rrg_analyzer.py 1h telegram
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import yfinance as yf
import pandas as pd
import numpy as np

# Add market-analyzer to path for RRG functions
sys.path.insert(0, '/root/clawd/projects/market-analyzer')
from rrg_rs_analyzer import calculate_rrg_values, get_rrg_quadrant

# ============================================================================
# Configuration
# ============================================================================

def load_hk_symbols():
    """Load HK symbols from HSI constituents JSON"""
    try:
        with open('/root/clawd/hsi_constituents.json', 'r') as f:
            constituents = json.load(f)
            return list(constituents.keys())
    except:
        # Fallback list
        return [
            '0001.HK', '0005.HK', '0011.HK', '0016.HK', '0027.HK', '0066.HK',
            '0175.HK', '0241.HK', '0267.HK', '0268.HK', '0288.HK', '0386.HK',
            '0388.HK', '0669.HK', '0688.HK', '0700.HK', '0762.HK', '0823.HK',
            '0857.HK', '0883.HK', '0939.HK', '0941.HK', '0968.HK', '0981.HK',
            '1038.HK', '1093.HK', '1177.HK', '1211.HK', '1299.HK', '1398.HK',
            '1810.HK', '1876.HK', '1928.HK', '2007.HK', '2018.HK', '2269.HK',
            '2313.HK', '2318.HK', '2319.HK', '2331.HK', '2382.HK', '2388.HK',
            '2628.HK', '3690.HK', '3968.HK', '3988.HK', '6098.HK', '6618.HK',
            '6862.HK', '9618.HK', '9888.HK', '9988.HK', '9999.HK'
        ]

HK_SYMBOLS = load_hk_symbols()
BENCHMARK = '^HSI'  # Hang Seng Index

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '1016466977')
JC_ALGOS_CHANNEL = '-1003796838384'  # JC Algos NEW channel


# ============================================================================
# BB Squeeze Detection
# ============================================================================

def calculate_bb_squeeze(df: pd.DataFrame, bb_period: int = 20, bb_std: float = 2.0,
                         kc_period: int = 20, kc_mult: float = 1.5) -> pd.DataFrame:
    """Calculate Bollinger Band Squeeze indicators"""
    
    # Bollinger Bands
    df['BB_MID'] = df['Close'].rolling(window=bb_period).mean()
    df['BB_STD'] = df['Close'].rolling(window=bb_period).std()
    df['BB_UPPER'] = df['BB_MID'] + (bb_std * df['BB_STD'])
    df['BB_LOWER'] = df['BB_MID'] - (bb_std * df['BB_STD'])
    df['BB_WIDTH'] = (df['BB_UPPER'] - df['BB_LOWER']) / df['BB_MID']
    
    # Keltner Channels
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.maximum(
            abs(df['High'] - df['Close'].shift(1)),
            abs(df['Low'] - df['Close'].shift(1))
        )
    )
    df['ATR'] = df['TR'].rolling(window=kc_period).mean()
    df['KC_MID'] = df['Close'].rolling(window=kc_period).mean()
    df['KC_UPPER'] = df['KC_MID'] + (kc_mult * df['ATR'])
    df['KC_LOWER'] = df['KC_MID'] - (kc_mult * df['ATR'])
    
    # Squeeze detection (BB inside KC)
    df['SQUEEZE'] = (df['BB_LOWER'] > df['KC_LOWER']) & (df['BB_UPPER'] < df['KC_UPPER'])
    
    # RSI for direction
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Momentum (for squeeze direction)
    df['MOM'] = df['Close'] - df['Close'].rolling(window=12).mean()
    
    return df


def detect_squeezes(symbols: List[str], timeframe: str = '1h', 
                    lookback_days: int = 60) -> Dict[str, List[dict]]:
    """Detect BB squeezes for a list of symbols"""
    
    # Map timeframe to yfinance interval
    interval_map = {
        '1h': '1h',
        '4h': '1h',  # yfinance doesn't have 4h, we'll resample
        '1d': '1d',
    }
    interval = interval_map.get(timeframe, '1h')
    
    end = datetime.now()
    start = end - timedelta(days=lookback_days)
    
    results = {'bullish': [], 'bearish': [], 'neutral': []}
    
    print(f"Scanning {len(symbols)} HK symbols for {timeframe} squeeze...", file=sys.stderr)
    
    # Download all data at once for efficiency
    try:
        data = yf.download(symbols, start=start, end=end, interval=interval, 
                          progress=False, auto_adjust=True, group_by='ticker')
    except Exception as e:
        print(f"Error downloading data: {e}", file=sys.stderr)
        return results
    
    for symbol in symbols:
        try:
            # Extract symbol data
            if len(symbols) == 1:
                df = data.copy()
            elif symbol in data.columns.get_level_values(0):
                df = data[symbol].copy()
            else:
                continue
            
            if df.empty or len(df) < 30:
                continue
            
            # Resample if 4h
            if timeframe == '4h':
                df = df.resample('4h').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 
                    'Close': 'last', 'Volume': 'sum'
                }).dropna()
            
            # Calculate squeeze
            df = calculate_bb_squeeze(df)
            
            # Check if in squeeze
            if not df['SQUEEZE'].iloc[-1]:
                continue
            
            # Get current values
            price = df['Close'].iloc[-1]
            bbw = df['BB_WIDTH'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            mom = df['MOM'].iloc[-1]
            bb_upper = df['BB_UPPER'].iloc[-1]
            bb_lower = df['BB_LOWER'].iloc[-1]
            prev_close = df['Close'].iloc[-2] if len(df) > 1 else price
            change_pct = (price - prev_close) / prev_close * 100
            
            # Format symbol for display (remove .HK suffix)
            display_symbol = symbol.replace('.HK', '')
            
            info = {
                'symbol': display_symbol,
                'full_symbol': symbol,
                'price': round(price, 2),
                'change_pct': round(change_pct, 2),
                'bbw': round(bbw, 4),
                'rsi': round(rsi, 1),
                'momentum': mom
            }
            
            # Classify by RSI/momentum + breakout
            # Bullish: RSI > 50, Momentum > 0, AND Close > BB Upper (breakout)
            # Bearish: RSI < 50, Momentum < 0, AND Close < BB Lower (breakout)
            if rsi > 50 and mom > 0 and price > bb_upper:
                results['bullish'].append(info)
            elif rsi < 50 and mom < 0 and price < bb_lower:
                results['bearish'].append(info)
            else:
                results['neutral'].append(info)
                
        except Exception as e:
            continue
    
    # Sort by BBW (tighter = better)
    for category in results:
        results[category].sort(key=lambda x: x['bbw'])
    
    return results


# ============================================================================
# RRG Analysis
# ============================================================================

def analyze_rrg_quadrants(symbols: List[str], benchmark: str = '^HSI') -> Dict[str, List[dict]]:
    """Analyze RRG quadrants for symbols"""
    
    end = datetime.now()
    start = end - timedelta(days=180)
    
    # Convert display symbols back to full symbols
    full_symbols = [s if '.HK' in s else f"{s}.HK" for s in symbols]
    
    # Download data
    all_symbols = full_symbols + [benchmark]
    data = yf.download(all_symbols, start=start, end=end, progress=False, auto_adjust=True)
    
    # Handle data format
    if 'Close' in data.columns.get_level_values(0) if hasattr(data.columns, 'levels') else 'Close' in data.columns:
        try:
            data = data['Close']
        except:
            pass
    
    benchmark_data = data[benchmark]
    
    quadrants = {
        'leading': [],
        'improving': [],
        'weakening': [],
        'lagging': []
    }
    
    for i, symbol in enumerate(full_symbols):
        try:
            if symbol not in data.columns:
                continue
                
            asset_data = data[symbol].dropna()
            bench = benchmark_data.loc[asset_data.index]
            
            rs_ratio, rs_momentum = calculate_rrg_values(asset_data, bench)
            latest_ratio = rs_ratio.iloc[-1]
            latest_momentum = rs_momentum.iloc[-1]
            quadrant = get_rrg_quadrant(latest_ratio, latest_momentum)
            
            # Use display symbol (without .HK)
            display_symbol = symbols[i] if i < len(symbols) else symbol.replace('.HK', '')
            
            info = {
                'symbol': display_symbol,
                'rs_ratio': round(latest_ratio, 1),
                'rs_momentum': round(latest_momentum, 1)
            }
            
            quadrants[quadrant.lower()].append(info)
            
        except Exception as e:
            continue
    
    return quadrants


# ============================================================================
# Combined Analysis
# ============================================================================

def analyze_squeeze_rrg(timeframe: str = '1h') -> Dict:
    """Run combined BB Squeeze + RRG analysis"""
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    # Step 1: Detect squeezes
    squeezes = detect_squeezes(HK_SYMBOLS, timeframe)
    
    # Step 2: Analyze RRG for bullish squeezes
    bullish_symbols = [s['symbol'] for s in squeezes['bullish']]
    
    if bullish_symbols:
        rrg_results = analyze_rrg_quadrants(bullish_symbols)
    else:
        rrg_results = {'leading': [], 'improving': [], 'weakening': [], 'lagging': []}
    
    # Step 3: Merge squeeze data with RRG data
    squeeze_lookup = {s['symbol']: s for s in squeezes['bullish']}
    
    result = {
        'timestamp': timestamp,
        'timeframe': timeframe,
        'total_squeezes': len(squeezes['bullish']) + len(squeezes['bearish']) + len(squeezes['neutral']),
        'bullish_count': len(squeezes['bullish']),
        'bearish_count': len(squeezes['bearish']),
        'neutral_count': len(squeezes['neutral']),
        'bullish_rrg': {
            'leading': [],
            'improving': [],
            'weakening': [],
            'lagging': []
        },
        'bearish_squeezes': squeezes['bearish'][:10],  # Top 10
        'neutral_squeezes': squeezes['neutral'][:5]    # Top 5
    }
    
    # Merge RRG with squeeze data
    for quadrant in ['leading', 'improving', 'weakening', 'lagging']:
        for rrg_info in rrg_results[quadrant]:
            symbol = rrg_info['symbol']
            if symbol in squeeze_lookup:
                merged = {**squeeze_lookup[symbol], **rrg_info}
                result['bullish_rrg'][quadrant].append(merged)
    
    return result


# ============================================================================
# Output Formatters
# ============================================================================

def format_telegram(result: Dict) -> str:
    """Format result for Telegram"""
    
    lines = [
        f"🇭🇰 **港股 BB Squeeze + RRG 分析**",
        f"📅 {result['timestamp']} | {result['timeframe']}",
        f"Scanned: {len(HK_SYMBOLS)} symbols | Found: {result['total_squeezes']} squeezes",
        "",
        "━━━━━━━━━━━━━━━",
        "",
        f"📈 **BULLISH SQUEEZE ({result['bullish_count']})** 已突破上軌",
        ""
    ]
    
    # Leading
    leading = result['bullish_rrg']['leading']
    lines.append(f"🟢 **LEADING 領先 ({len(leading)})**")
    if leading:
        for s in leading[:10]:
            lines.append(f"• {s['symbol']} ${s['price']} BBW:{s['bbw']} RS:{s['rs_ratio']}")
    else:
        lines.append("  (none)")
    lines.append("")
    
    # Improving
    improving = result['bullish_rrg']['improving']
    lines.append(f"🔵 **IMPROVING 改善中 ({len(improving)})**")
    if improving:
        for s in improving[:10]:
            lines.append(f"• {s['symbol']} ${s['price']} BBW:{s['bbw']} RS:{s['rs_ratio']}")
    else:
        lines.append("  (none)")
    lines.append("")
    
    # Weakening
    weakening = result['bullish_rrg']['weakening']
    lines.append(f"🟡 **WEAKENING 轉弱 ({len(weakening)})**")
    if weakening:
        for s in weakening[:10]:
            lines.append(f"• {s['symbol']} ${s['price']} BBW:{s['bbw']} RS:{s['rs_ratio']}")
    else:
        lines.append("  (none)")
    lines.append("")
    
    # Lagging
    lagging = result['bullish_rrg']['lagging']
    lines.append(f"🔴 **LAGGING 落後 ({len(lagging)})**")
    if lagging:
        for s in lagging[:10]:
            lines.append(f"• {s['symbol']} ${s['price']} BBW:{s['bbw']} RS:{s['rs_ratio']}")
    else:
        lines.append("  (none)")
    
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━",
        "",
        f"📉 **BEARISH SQUEEZE ({result['bearish_count']})** 已跌穿下軌:",
    ])
    for s in result['bearish_squeezes'][:5]:
        lines.append(f"• {s['symbol']} ${s['price']} BBW:{s['bbw']} RSI:{s['rsi']}")
    
    if not result['bearish_squeezes']:
        lines.append("  (none)")
    
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━",
        "🐷 Oracle | RS>100=強於恒指"
    ])
    
    return "\n".join(lines)


def send_telegram(message: str, chat_id: str = None):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        print("No TELEGRAM_BOT_TOKEN set", file=sys.stderr)
        return False
    
    chat_id = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        resp = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        })
        return resp.ok
    except Exception as e:
        print(f"Telegram error: {e}", file=sys.stderr)
        return False


# ============================================================================
# Main
# ============================================================================

def main():
    timeframe = sys.argv[1] if len(sys.argv) > 1 else '1h'
    output_mode = sys.argv[2] if len(sys.argv) > 2 else 'text'
    
    result = analyze_squeeze_rrg(timeframe)
    
    if output_mode == 'json':
        print(json.dumps(result, indent=2))
    elif output_mode == 'telegram':
        msg = format_telegram(result)
        print(msg)
        send_telegram(msg, TELEGRAM_CHAT_ID)
        send_telegram(msg, JC_ALGOS_CHANNEL)
    else:
        print(format_telegram(result))


if __name__ == '__main__':
    main()
