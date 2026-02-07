#!/usr/bin/env python3
"""
BB Squeeze + RRG Quadrant Analyzer
Combines BB Squeeze detection with RRG relative strength analysis

Usage:
    python3 squeeze_rrg_analyzer.py [timeframe] [output]
    
    timeframe: 1h, 4h, 1d (default: 1h)
    output: json, telegram, text (default: text)
    
Example:
    python3 squeeze_rrg_analyzer.py 1h telegram
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

# Merged US Stock Universe (323 symbols) - combined from both scanners
US_SYMBOLS = [
    'AAPL', 'ABBV', 'ABNB', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP',
    'AES', 'AFL', 'AIG', 'AJG', 'ALGN', 'ALL', 'AMAT', 'AMD', 'AMGN', 'AMP',
    'AMPX', 'AMT', 'AMZN', 'ANET', 'AON', 'APA', 'APD', 'APH', 'APO', 'APP',
    'ARM', 'ASML', 'ATO', 'AVB', 'AVGO', 'AWK', 'AXON', 'AXP', 'AZN', 'AZO',
    'BA', 'BAC', 'BDX', 'BIIB', 'BK', 'BKNG', 'BKR', 'BLK', 'BMY', 'BRK-B',
    'BSX', 'BX', 'C', 'CAG', 'CARR', 'CAT', 'CB', 'CCEP', 'CCL', 'CDNS',
    'CDW', 'CEG', 'CF', 'CHD', 'CHTR', 'CI', 'CL', 'CLF', 'CLX', 'CMCSA',
    'CME', 'CMG', 'CMS', 'COF', 'COIN', 'COP', 'COR', 'COST', 'CPB', 'CPRT',
    'CRM', 'CRWD', 'CSCO', 'CSGP', 'CSX', 'CTAS', 'CTSH', 'CVS', 'CVX', 'D',
    'DASH', 'DDOG', 'DE', 'DELL', 'DHR', 'DIA', 'DIS', 'DLR', 'DLTR', 'DPZ',
    'DTE', 'DUK', 'DVN', 'DXCM', 'EA', 'ECL', 'ED', 'EEM', 'EIX', 'ELV',
    'EMR', 'EOG', 'EOSE', 'EQIX', 'EQR', 'ES', 'ETN', 'ETR', 'EVRG', 'EXC',
    'F', 'FANG', 'FAST', 'FCX', 'FDX', 'FE', 'FRT', 'FTNT', 'FUTU', 'FXI',
    'GD', 'GDX', 'GE', 'GEHC', 'GEV', 'GFS', 'GILD', 'GIS', 'GM', 'GOLD',
    'GOOG', 'GOOGL', 'GS', 'GWW', 'HAL', 'HCA', 'HD', 'HLT', 'HON', 'HRL',
    'HST', 'HSY', 'HWM', 'IBM', 'ICE', 'IDXX', 'INTC', 'INTU', 'ISRG', 'ITW',
    'IWM', 'JCI', 'JNJ', 'JPM', 'KDP', 'KHC', 'KKR', 'KLAC', 'KMB', 'KMI',
    'KO', 'KR', 'LEN', 'LIN', 'LLY', 'LMT', 'LNG', 'LNT', 'LOW', 'LRCX',
    'LULU', 'MA', 'MAA', 'MAR', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT',
    'MELI', 'MET', 'META', 'MKC', 'MMC', 'MMM', 'MNST', 'MO', 'MPC', 'MRK',
    'MRVL', 'MS', 'MSFT', 'MSI', 'MSTR', 'MU', 'NDAQ', 'NEE', 'NEM', 'NFLX',
    'NI', 'NKE', 'NOC', 'NOW', 'NRG', 'NSC', 'NUE', 'NVDA', 'NVO', 'NXPI',
    'O', 'ODFL', 'OKE', 'ON', 'ORCL', 'ORLY', 'OXY', 'PANW', 'PAYX', 'PCAR',
    'PDD', 'PEP', 'PFE', 'PG', 'PGR', 'PH', 'PLD', 'PLTR', 'PM', 'PNC',
    'PPL', 'PSA', 'PSX', 'PWR', 'PYPL', 'QCOM', 'QQQ', 'RCL', 'REG', 'REGN',
    'ROP', 'ROST', 'RSG', 'RTX', 'SBUX', 'SCCO', 'SCHW', 'SHOP', 'SHW', 'SJM',
    'SLB', 'SMH', 'SNOW', 'SNPS', 'SO', 'SPG', 'SPGI', 'SPY', 'SRE', 'SYK',
    'SYY', 'T', 'TDG', 'TEAM', 'TFC', 'TGT', 'TJX', 'TMO', 'TMUS', 'TRV',
    'TSLA', 'TSM', 'TSN', 'TT', 'TTD', 'TTWO', 'TXN', 'UBER', 'ULTA', 'UNH',
    'UNP', 'UPS', 'USB', 'V', 'VLO', 'VRSK', 'VRTX', 'VST', 'VTR', 'VZ',
    'WBD', 'WDAY', 'WEC', 'WELL', 'WFC', 'WM', 'WMB', 'WMT', 'XEL', 'XLC',
    'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'XOM',
    'YUM', 'ZS', 'ZTS',
]

BENCHMARK = 'SPY'

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
    
    print(f"Scanning {len(symbols)} symbols for {timeframe} squeeze...", file=sys.stderr)
    
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
            prev_close = df['Close'].iloc[-2] if len(df) > 1 else price
            change_pct = (price - prev_close) / prev_close * 100
            
            info = {
                'symbol': symbol,
                'price': round(price, 2),
                'change_pct': round(change_pct, 2),
                'bbw': round(bbw, 4),
                'rsi': round(rsi, 1),
                'momentum': mom
            }
            
            # Get BB levels for breakout detection
            bb_upper = df['BB_UPPER'].iloc[-1]
            bb_lower = df['BB_LOWER'].iloc[-1]
            
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

def analyze_rrg_quadrants(symbols: List[str], benchmark: str = 'SPY') -> Dict[str, List[dict]]:
    """Analyze RRG quadrants for symbols"""
    
    end = datetime.now()
    start = end - timedelta(days=180)
    
    # Download data
    all_symbols = symbols + [benchmark]
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
    
    for symbol in symbols:
        try:
            if symbol not in data.columns:
                continue
                
            asset_data = data[symbol].dropna()
            bench = benchmark_data.loc[asset_data.index]
            
            rs_ratio, rs_momentum = calculate_rrg_values(asset_data, bench)
            latest_ratio = rs_ratio.iloc[-1]
            latest_momentum = rs_momentum.iloc[-1]
            quadrant = get_rrg_quadrant(latest_ratio, latest_momentum)
            
            info = {
                'symbol': symbol,
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
    squeezes = detect_squeezes(US_SYMBOLS, timeframe)
    
    # Step 2: Analyze RRG for bullish squeezes
    bullish_symbols = [s['symbol'] for s in squeezes['bullish']]
    
    if bullish_symbols:
        rrg_results = analyze_rrg_quadrants(bullish_symbols)
    else:
        rrg_results = {'leading': [], 'improving': [], 'weakening': [], 'lagging': []}
    
    # Step 2b: Analyze RRG for bearish squeezes too
    bearish_symbols = [s['symbol'] for s in squeezes['bearish']]
    
    if bearish_symbols:
        bearish_rrg_results = analyze_rrg_quadrants(bearish_symbols)
    else:
        bearish_rrg_results = {'leading': [], 'improving': [], 'weakening': [], 'lagging': []}
    
    # Create lookup for bearish RRG quadrants
    bearish_rrg_lookup = {}
    for quadrant in ['leading', 'improving', 'weakening', 'lagging']:
        for info in bearish_rrg_results[quadrant]:
            bearish_rrg_lookup[info['symbol']] = quadrant
    
    # Merge RRG quadrant into bearish squeezes
    for s in squeezes['bearish']:
        s['rrg_quadrant'] = bearish_rrg_lookup.get(s['symbol'], 'unknown')
    
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
        f"🔄 **BB Squeeze + RRG 分析**",
        f"📅 {result['timestamp']} | {result['timeframe']}",
        f"Scanned: 323 symbols | Found: {result['total_squeezes']} squeezes",
        "",
        "━━━━━━━━━━━━━━━",
        "",
        f"📈 **BULLISH SQUEEZE ({result['bullish_count']})**",
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
        f"📉 **BEARISH SQUEEZE ({result['bearish_count']})** Top 5:",
    ])
    rrg_labels = {'leading': '領先', 'improving': '改善中', 'weakening': '轉弱', 'lagging': '落後', 'unknown': '?'}
    for s in result['bearish_squeezes'][:5]:
        quadrant = rrg_labels.get(s.get('rrg_quadrant', 'unknown'), '?')
        lines.append(f"• {s['symbol']} ${s['price']} | RRG:{quadrant} | BBW:{s['bbw']} RSI:{s['rsi']}")
    
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━",
        "🐷 Oracle | RS>100=強於大市"
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
