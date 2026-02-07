#!/usr/bin/env python3
"""
Crypto BB Squeeze Scanner using TradingView MCP
Scans BINANCE/KUCOIN for Bollinger Band squeezes
"""

import json
import subprocess
import sys
from datetime import datetime

def call_mcporter_bollinger_scan(exchange="BINANCE", timeframe="4h", bbw_threshold=0.04, limit=100):
    """Call TradingView MCP bollinger_scan tool"""
    cmd = [
        "mcporter", "call", "tradingview.bollinger_scan",
        f'exchange:"{exchange}"',
        f'timeframe:"{timeframe}"',
        f'bbw_threshold:{bbw_threshold}',
        f'limit:{limit}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def call_mcporter_coin_analysis(symbol, exchange="BINANCE", timeframe="4h"):
    """Get detailed analysis for a specific coin"""
    cmd = [
        "mcporter", "call", "tradingview.coin_analysis",
        f'symbol:"{symbol}"',
        f'exchange:"{exchange}"',
        f'timeframe:"{timeframe}"'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        return None


def analyze_squeeze_opportunity(symbol, data, timeframe):
    """Analyze BB squeeze for trading opportunity"""
    
    if not data or 'indicators' not in data:
        return None
    
    ind = data['indicators']
    
    # Extract key metrics
    close = ind.get('close')
    bb_upper = ind.get('BB_upper')
    bb_lower = ind.get('BB_lower')
    sma20 = ind.get('SMA20')
    rsi = ind.get('RSI', 50)
    volume = ind.get('volume', 0)
    
    if not all([close, bb_upper, bb_lower, sma20]):
        return None
    
    # Calculate BB Width
    bb_width = (bb_upper - bb_lower) / sma20 if sma20 > 0 else 0
    
    # BB Position (where price is within the bands)
    bb_position = (close - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    
    # Determine opportunity type
    opportunity_type = "CONSOLIDATING"
    signal_strength = "WEAK"
    
    if bb_width < 0.02:  # Very tight squeeze
        signal_strength = "STRONG"
        if bb_position > 0.7 and rsi > 60:
            opportunity_type = "BULLISH_BREAKOUT_READY"
        elif bb_position < 0.3 and rsi < 40:
            opportunity_type = "BEARISH_BREAKDOWN_READY"
        else:
            opportunity_type = "TIGHT_SQUEEZE_NEUTRAL"
    elif bb_width < 0.03:  # Moderate squeeze
        signal_strength = "MODERATE"
        if bb_position > 0.6:
            opportunity_type = "BULLISH_SQUEEZE"
        elif bb_position < 0.4:
            opportunity_type = "BEARISH_SQUEEZE"
    
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'close': close,
        'bb_width': bb_width,
        'bb_position': bb_position,
        'bb_upper': bb_upper,
        'bb_lower': bb_lower,
        'sma20': sma20,
        'rsi': rsi,
        'volume': volume,
        'opportunity_type': opportunity_type,
        'signal_strength': signal_strength,
        'change_percent': data.get('changePercent', 0)
    }


def scan_crypto_bb_squeeze(exchange="BINANCE", timeframe="4h", bbw_threshold=0.04):
    """Scan crypto markets for BB squeeze opportunities"""
    
    print("=" * 100)
    print(f"🔍 CRYPTO BOLLINGER BAND SQUEEZE SCANNER")
    print("=" * 100)
    print(f"Exchange: {exchange}")
    print(f"Timeframe: {timeframe}")
    print(f"BB Width Threshold: {bbw_threshold}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S HKT')}")
    print("=" * 100)
    print()
    
    # Step 1: Get all coins with BB squeeze
    print(f"📊 Scanning {exchange} for BB squeezes...")
    squeeze_coins = call_mcporter_bollinger_scan(exchange, timeframe, bbw_threshold, 100)
    
    if not squeeze_coins:
        print("❌ No data received from scanner")
        return []
    
    # Parse results
    if isinstance(squeeze_coins, dict) and 'symbol' in squeeze_coins:
        squeeze_coins = [squeeze_coins]
    elif not isinstance(squeeze_coins, list):
        print(f"⚠️  Unexpected data format: {type(squeeze_coins)}")
        return []
    
    print(f"✅ Found {len(squeeze_coins)} coins with BB squeeze")
    print()
    
    # Step 2: Analyze each coin for trading opportunity
    opportunities = []
    
    for i, coin_data in enumerate(squeeze_coins, 1):
        symbol = coin_data.get('symbol', 'UNKNOWN')
        print(f"[{i}/{len(squeeze_coins)}] Analyzing {symbol}...", end=" ")
        
        opportunity = analyze_squeeze_opportunity(symbol, coin_data, timeframe)
        
        if opportunity:
            opportunities.append(opportunity)
            print(f"✅ {opportunity['opportunity_type']} ({opportunity['signal_strength']})")
        else:
            print("⚠️  Analysis failed")
    
    print()
    print("=" * 100)
    print(f"📊 SCAN COMPLETE - Found {len(opportunities)} trading opportunities")
    print("=" * 100)
    print()
    
    return opportunities


def print_opportunities(opportunities):
    """Print formatted trading opportunities"""
    
    if not opportunities:
        print("No BB squeeze opportunities found.")
        return
    
    # Sort by signal strength and BB width
    strength_order = {"STRONG": 0, "MODERATE": 1, "WEAK": 2}
    opportunities.sort(key=lambda x: (strength_order.get(x['signal_strength'], 3), x['bb_width']))
    
    print()
    print("🎯 TRADING OPPORTUNITIES")
    print("=" * 100)
    print()
    
    bullish = [o for o in opportunities if 'BULLISH' in o['opportunity_type']]
    bearish = [o for o in opportunities if 'BEARISH' in o['opportunity_type']]
    neutral = [o for o in opportunities if o not in bullish and o not in bearish]
    
    # Print BULLISH opportunities
    if bullish:
        print(f"📈 BULLISH SETUPS ({len(bullish)})")
        print("-" * 100)
        for i, opp in enumerate(bullish, 1):
            print_opportunity_detail(i, opp)
        print()
    
    # Print BEARISH opportunities
    if bearish:
        print(f"📉 BEARISH SETUPS ({len(bearish)})")
        print("-" * 100)
        for i, opp in enumerate(bearish, 1):
            print_opportunity_detail(i, opp)
        print()
    
    # Print NEUTRAL/CONSOLIDATING
    if neutral:
        print(f"⏳ CONSOLIDATING ({len(neutral)})")
        print("-" * 100)
        for i, opp in enumerate(neutral, 1):
            print_opportunity_detail(i, opp, brief=True)
        print()
    
    print("=" * 100)
    
    # Save to JSON
    output_file = '/root/clawd/crypto_bb_squeeze_results.json'
    with open(output_file, 'w') as f:
        json.dump(opportunities, f, indent=2, default=str)
    
    print(f"📁 Results saved to: {output_file}")
    print()


def print_opportunity_detail(num, opp, brief=False):
    """Print detailed opportunity information"""
    
    strength_emoji = {"STRONG": "🔥", "MODERATE": "⚡", "WEAK": "💡"}
    
    print(f"{num}. {opp['symbol']} {strength_emoji.get(opp['signal_strength'], '')} {opp['signal_strength']}")
    print(f"   Type: {opp['opportunity_type']}")
    print(f"   Price: ${opp['close']:.4f} | Change: {opp['change_percent']:+.2f}%")
    print(f"   BB Width: {opp['bb_width']:.4f} | Position: {opp['bb_position']:.1%}")
    print(f"   RSI: {opp['rsi']:.1f}")
    
    if not brief:
        # Trading recommendation
        if 'BULLISH' in opp['opportunity_type']:
            print(f"   ")
            print(f"   📈 LONG SETUP:")
            print(f"      Entry: Breakout above ${opp['bb_upper']:.4f}")
            print(f"      Stop Loss: ${opp['bb_lower']:.4f}")
            print(f"      Target 1: ${opp['bb_upper'] + (opp['bb_upper'] - opp['sma20']):.4f}")
            print(f"      Risk/Reward: ~1:2")
        elif 'BEARISH' in opp['opportunity_type']:
            print(f"   ")
            print(f"   📉 SHORT SETUP:")
            print(f"      Entry: Breakdown below ${opp['bb_lower']:.4f}")
            print(f"      Stop Loss: ${opp['bb_upper']:.4f}")
            print(f"      Target 1: ${opp['bb_lower'] - (opp['sma20'] - opp['bb_lower']):.4f}")
            print(f"      Risk/Reward: ~1:2")
        else:
            print(f"      ⏳ Wait for directional breakout")
    
    print()


def main():
    """Main execution"""
    
    # Parse arguments
    exchange = sys.argv[1] if len(sys.argv) > 1 else "BINANCE"
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "4h"
    bbw_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.04
    
    # Run scan
    opportunities = scan_crypto_bb_squeeze(exchange, timeframe, bbw_threshold)
    
    # Print results
    print_opportunities(opportunities)
    
    print("✅ Crypto BB Squeeze Scan Complete!")
    print()
    print("💡 TIP: Run with different exchanges:")
    print("   python3 crypto_bb_squeeze_scanner.py KUCOIN 1h 0.03")
    print("   python3 crypto_bb_squeeze_scanner.py BYBIT 15m 0.04")
    

if __name__ == "__main__":
    main()
