#!/usr/bin/env python3
"""
US Stock Bollinger Band Squeeze Scanner
Scans US stocks for BB squeeze opportunities
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
import sys

# US Stock List
US_STOCKS = [
    "AAPL", "ABBV", "ABNB", "ABT", "ACN", "ADBE", "ADI", "ADP", "ADSK", "AEP",
    "AFL", "AIG", "AJG", "ALGN", "ALL", "AMAT", "AMD", "AMGN", "AMP", "AMPX",
    "AMT", "AMZN", "ANET", "AON", "APA", "APD", "APH", "APO", "APP", "ARM",
    "ASML", "AVGO", "AXON", "AXP", "AZN", "AZO", "BA", "BAC", "BDX", "BIIB",
    "BK", "BKNG", "BKR", "BLK", "BMY", "BRK-B", "BSX", "BX", "C", "CARR",
    "CAT", "CB", "CCEP", "CCL", "CDNS", "CDW", "CEG", "CF", "CHTR", "CI",
    "CL", "CMCSA", "CME", "CMG", "COF", "COIN", "COP", "COR", "COST", "CPRT",
    "CRM", "CRWD", "CSCO", "CSGP", "CSX", "CTAS", "CTSH", "CVS", "CVX", "DASH",
    "DDOG", "DE", "DELL", "DHR", "DIS", "DLR", "DLTR", "DUK", "DVN", "DXCM",
    "EA", "ECL", "ELV", "EMR", "EOG", "EOSE", "EQIX", "ETN", "EXC", "F",
    "FANG", "FAST", "FCX", "FDX", "FTNT", "FUTU", "GD", "GE", "GEHC", "GEV",
    "GFS", "GILD", "GIS", "GM", "GOOG", "GOOGL", "GS", "GWW", "HAL", "HCA",
    "HD", "HLT", "HON", "HSY", "HWM", "IBM", "ICE", "IDXX", "INTC", "INTU",
    "ISRG", "ITW", "IWM", "JCI", "JNJ", "JPM", "KDP", "KHC", "KKR", "KLAC",
    "KMB", "KMI", "KO", "LEN", "LIN", "LLY", "LMT", "LOW", "LRCX", "LULU",
    "MA", "MAR", "MCD", "MCHP", "MCK", "MCO", "MDLZ", "MDT", "MELI", "MET",
    "META", "MMC", "MMM", "MNST", "MO", "MPC", "MRK", "MRVL", "MS", "MSFT",
    "MSI", "MSTR", "MU", "NDAQ", "NEE", "NEM", "NFLX", "NKE", "NOC", "NOW",
    "NRG", "NSC", "NVDA", "NVO", "NXPI", "O", "ODFL", "OKE", "ON", "ORCL",
    "ORLY", "OXY", "PANW", "PAYX", "PCAR", "PDD", "PEP", "PFE", "PG", "PGR",
    "PH", "PLD", "PLTR", "PM", "PNC", "PSA", "PSX", "PWR", "PYPL", "QCOM",
    "RCL", "REGN", "ROP", "ROST", "RSG", "RTX", "SBUX", "SCHW", "SHOP", "SHW",
    "SLB", "SMH", "SNOW", "SNPS", "SO", "SPG", "SPGI", "SRE", "SYK", "T",
    "TDG", "TEAM", "TFC", "TGT", "TJX", "TMO", "TMUS", "TRV", "TSLA", "TSM",
    "TT", "TTD", "TTWO", "TXN", "UBER", "ULTA", "UNH", "UNP", "UPS", "USB",
    "V", "VLO", "VRSK", "VRTX", "VST", "VZ", "WBD", "WDAY", "WELL", "WFC",
    "WM", "WMB", "WMT", "XEL", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP",
    "XLRE", "XLU", "XLV", "XLY", "XOM", "YUM", "ZS", "ZTS"
]

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    df['SMA'] = df['Close'].rolling(window=period).mean()
    df['STD'] = df['Close'].rolling(window=period).std()
    df['BB_Upper'] = df['SMA'] + (std_dev * df['STD'])
    df['BB_Lower'] = df['SMA'] - (std_dev * df['STD'])
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA']
    df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    return df

def calculate_rsi(df, period=14):
    """Calculate RSI"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def analyze_stock(symbol, period='3mo', interval='1d'):
    """Analyze a single stock for BB squeeze"""
    try:
        if interval == '1wk':
            period = '2y'
        elif interval == '1mo':
            period = '5y'
        
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        
        if df.empty or len(df) < 30:
            return None
        
        df = calculate_bollinger_bands(df)
        df = calculate_rsi(df)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        bb_width = latest['BB_Width']
        is_squeeze = bb_width < 0.04
        
        price = latest['Close']
        sma = latest['SMA']
        rsi = latest['RSI']
        volume = latest['Volume']
        change_pct = ((price - prev['Close']) / prev['Close'] * 100) if prev['Close'] > 0 else 0
        
        opportunity = analyze_opportunity(latest, bb_width, is_squeeze)
        
        return {
            'symbol': symbol,
            'price': float(price),
            'change_pct': float(change_pct),
            'bb_width': float(bb_width),
            'bb_position': float(latest['BB_Position']) if not pd.isna(latest['BB_Position']) else 0.5,
            'bb_upper': float(latest['BB_Upper']),
            'bb_lower': float(latest['BB_Lower']),
            'sma': float(sma),
            'rsi': float(rsi),
            'volume': int(volume),
            'is_squeeze': is_squeeze,
            'opportunity': opportunity,
            'signal_strength': get_signal_strength(bb_width, latest['BB_Position'], rsi)
        }
        
    except Exception as e:
        return None

def analyze_opportunity(latest, bb_width, is_squeeze):
    """Determine trading opportunity type"""
    if not is_squeeze:
        return "NO_SQUEEZE"
    
    bb_pos = latest['BB_Position']
    rsi = latest['RSI']
    
    if bb_width < 0.02:
        if bb_pos > 0.7 and rsi > 60:
            return "BREAKOUT_UP_IMMINENT"
        elif bb_pos < 0.3 and rsi < 40:
            return "BREAKDOWN_IMMINENT"
        else:
            return "TIGHT_CONSOLIDATION"
    elif bb_width < 0.03:
        if bb_pos > 0.6 and rsi > 55:
            return "BULLISH_SQUEEZE"
        elif bb_pos < 0.4 and rsi < 45:
            return "BEARISH_SQUEEZE"
        else:
            return "NEUTRAL_SQUEEZE"
    else:
        if bb_pos > 0.5:
            return "MILD_BULLISH"
        else:
            return "MILD_BEARISH"

def get_signal_strength(bb_width, bb_position, rsi):
    """Determine signal strength"""
    if bb_width < 0.02:
        return "STRONG"
    elif bb_width < 0.03:
        return "MODERATE"
    else:
        return "WEAK"

def scan_us_stocks(interval='1d', quiet=False):
    """Scan all US stocks"""
    
    if not quiet:
        print("=" * 120)
        print(f"🇺🇸 US STOCK - BOLLINGER BAND SQUEEZE SCANNER")
        print("=" * 120)
        print(f"Total Stocks: {len(US_STOCKS)}")
        print(f"Interval: {interval}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 120)
        print()
    
    results = []
    squeeze_found = 0
    
    for i, symbol in enumerate(US_STOCKS, 1):
        if not quiet:
            print(f"[{i}/{len(US_STOCKS)}] {symbol:12}", end=" ")
        
        analysis = analyze_stock(symbol, interval=interval)
        
        if analysis:
            if analysis['is_squeeze']:
                results.append(analysis)
                squeeze_found += 1
                if not quiet:
                    print(f"✅ SQUEEZE! {analysis['opportunity']:25} ({analysis['signal_strength']})")
            else:
                if not quiet:
                    print(f"   No squeeze (BBW: {analysis['bb_width']:.4f})")
        else:
            if not quiet:
                print(f"   ⚠️  Data unavailable")
    
    if not quiet:
        print()
        print("=" * 120)
        print(f"📊 SCAN COMPLETE")
        print(f"   Total Scanned: {len(US_STOCKS)}")
        print(f"   Squeezes Found: {squeeze_found}")
        print(f"   Hit Rate: {(squeeze_found/len(US_STOCKS)*100):.1f}%")
        print("=" * 120)
        print()
    
    return results

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "🇺🇸 US BB Squeeze Scan\n\n❌ No squeeze opportunities found."
    
    # Sort by signal strength
    strength_order = {"STRONG": 0, "MODERATE": 1, "WEAK": 2}
    results.sort(key=lambda x: (strength_order.get(x['signal_strength'], 3), x['bb_width']))
    
    bullish = [r for r in results if 'BREAKOUT_UP' in r['opportunity'] or 'BULLISH' in r['opportunity']]
    bearish = [r for r in results if 'BREAKDOWN' in r['opportunity'] or 'BEARISH' in r['opportunity']]
    neutral = [r for r in results if r not in bullish and r not in bearish]
    
    msg = f"🇺🇸 US BB Squeeze Scan\n"
    msg += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
    msg += f"Found: {len(results)} squeezes\n\n"
    
    if bullish:
        msg += f"📈 BULLISH ({len(bullish)})\n"
        for r in bullish[:10]:
            emoji = "🔥" if r['signal_strength'] == "STRONG" else "⚡" if r['signal_strength'] == "MODERATE" else "💡"
            msg += f"{emoji} {r['symbol']} ${r['price']:.2f} ({r['change_pct']:+.1f}%)\n"
            msg += f"   BBW:{r['bb_width']:.3f} RSI:{r['rsi']:.0f}\n"
        msg += "\n"
    
    if bearish:
        msg += f"📉 BEARISH ({len(bearish)})\n"
        for r in bearish[:10]:
            emoji = "🔥" if r['signal_strength'] == "STRONG" else "⚡" if r['signal_strength'] == "MODERATE" else "💡"
            msg += f"{emoji} {r['symbol']} ${r['price']:.2f} ({r['change_pct']:+.1f}%)\n"
            msg += f"   BBW:{r['bb_width']:.3f} RSI:{r['rsi']:.0f}\n"
        msg += "\n"
    
    if neutral:
        msg += f"⏳ NEUTRAL ({len(neutral)})\n"
        for r in neutral[:5]:
            msg += f"   {r['symbol']} ${r['price']:.2f} BBW:{r['bb_width']:.3f}\n"
    
    return msg

def main():
    """Main execution"""
    interval = sys.argv[1] if len(sys.argv) > 1 else '1d'
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'full'
    
    if interval not in ['1d', '1h', '1wk', '1mo']:
        print(f"❌ Invalid interval: {interval}")
        print("Valid intervals: 1d (daily), 1h (hourly), 1wk (weekly), 1mo (monthly)")
        sys.exit(1)
    
    quiet = output_format == 'telegram'
    results = scan_us_stocks(interval, quiet=quiet)
    
    if output_format == 'telegram':
        print(format_telegram_message(results))
    else:
        # Full output
        if results:
            print("\n🎯 TRADING OPPORTUNITIES\n")
            
            bullish = [r for r in results if 'BREAKOUT_UP' in r['opportunity'] or 'BULLISH' in r['opportunity']]
            bearish = [r for r in results if 'BREAKDOWN' in r['opportunity'] or 'BEARISH' in r['opportunity']]
            
            if bullish:
                print(f"📈 BULLISH SETUPS ({len(bullish)})")
                print("-" * 80)
                for r in bullish:
                    print(f"  {r['symbol']:8} ${r['price']:8.2f} | {r['opportunity']:25} | BBW:{r['bb_width']:.4f} RSI:{r['rsi']:.1f}")
                print()
            
            if bearish:
                print(f"📉 BEARISH SETUPS ({len(bearish)})")
                print("-" * 80)
                for r in bearish:
                    print(f"  {r['symbol']:8} ${r['price']:8.2f} | {r['opportunity']:25} | BBW:{r['bb_width']:.4f} RSI:{r['rsi']:.1f}")
                print()
        
        # Save results
        output_file = '/root/clawd/us_bb_squeeze_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 Results saved to: {output_file}")
    
    print()

if __name__ == "__main__":
    main()
