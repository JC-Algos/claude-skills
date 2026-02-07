#!/usr/bin/env python3
"""
RRG Quadrant Strategy Backtest v2
=================================
Entry: Stock emerges from Lagging to Improving/Leading for 2+ days, buy Day 3 open
Exit: Falls back to Lagging OR trailing SL based on ATR
TP: 10 ATR with dynamic trailing
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import json
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

def load_hk_stocks():
    """Load all HK stocks from multiple sources"""
    stocks = {}
    
    # Try HSI constituents
    try:
        with open('/root/clawd/hsi_constituents.json', 'r') as f:
            stocks.update(json.load(f))
    except:
        pass
    
    # Try full HK stock list
    try:
        with open('/root/clawd/hk_stocks_full.json', 'r') as f:
            stocks.update(json.load(f))
    except:
        pass
    
    # Fallback to major stocks
    if not stocks:
        stocks = {
            '0700.HK': 'Tencent', '9988.HK': 'Alibaba', '0005.HK': 'HSBC',
            '1810.HK': 'Xiaomi', '9618.HK': 'JD.com', '0388.HK': 'HKEX',
            '2318.HK': 'Ping An', '0941.HK': 'China Mobile', '0883.HK': 'CNOOC',
            '1299.HK': 'AIA', '0027.HK': 'Galaxy', '0016.HK': 'SHK PPT',
            '0001.HK': 'CKH Holdings', '0011.HK': 'Hang Seng Bank',
            '0002.HK': 'CLP', '0003.HK': 'HK Gas', '0006.HK': 'Power Assets',
            '0012.HK': 'Henderson', '0017.HK': 'New World', '0066.HK': 'MTR',
            '0101.HK': 'Hang Lung', '0175.HK': 'Geely', '0241.HK': 'Alibaba Health',
            '0267.HK': 'CITIC', '0288.HK': 'WH Group', '0386.HK': 'Sinopec',
            '0688.HK': 'China Overseas', '0762.HK': 'China Unicom',
            '0857.HK': 'PetroChina', '0868.HK': 'Xinyi Glass',
            '0881.HK': 'Zhongsheng', '0960.HK': 'Longfor', '0968.HK': 'Xinyi Solar',
            '1038.HK': 'CKI Holdings', '1044.HK': 'Hengan', '1093.HK': 'CSPC Pharma',
            '1109.HK': 'China Resources', '1113.HK': 'CK Asset',
            '1177.HK': 'Sino Biopharm', '1211.HK': 'BYD', '1398.HK': 'ICBC',
            '1876.HK': 'Budweiser', '1928.HK': 'Sands China', '1997.HK': 'Wharf REIC',
            '2007.HK': 'Country Garden', '2018.HK': 'AAC Tech', '2020.HK': 'Anta Sports',
            '2269.HK': 'WuXi Bio', '2313.HK': 'Shenzhou', '2319.HK': 'Mengniu',
            '2331.HK': 'Li Ning', '2382.HK': 'Sunny Optical', '2388.HK': 'BOC HK',
            '2628.HK': 'China Life', '2688.HK': 'ENN Energy', '3328.HK': 'Bankcomm',
            '3690.HK': 'Meituan', '3968.HK': 'China Merchants Bank', '3988.HK': 'Bank of China',
            '6098.HK': 'CG Services', '6862.HK': 'Haidilao', '9618.HK': 'JD.com',
            '9633.HK': 'Nongfu Spring', '9888.HK': 'Baidu', '9961.HK': 'Trip.com',
            '9999.HK': 'NetEase',
        }
    
    return stocks

HK_STOCKS = load_hk_stocks()
BENCHMARK = '^HSI'

# Backtest Parameters
INITIAL_CAPITAL = 1_000_000
POSITION_SIZE = 0.05  # 5% per position
COMMISSION = 0.001    # 0.1%
STAMP_DUTY = 0.001    # 0.1%
SLIPPAGE = 0.002      # 0.2%

# =============================================================================
# INDICATOR CALCULATIONS
# =============================================================================

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_ma(data, period):
    """Simple Moving Average"""
    return data.rolling(window=period).mean()

# =============================================================================
# RRG CALCULATIONS
# =============================================================================

def calculate_rrg_values(asset_data, benchmark_data, 
                         ratio_short=10, ratio_long=26,
                         momentum_short=1, momentum_long=4):
    """Calculate RS-Ratio and RS-Momentum for RRG"""
    # Relative strength ratio
    sbr = asset_data / benchmark_data
    rs1 = calculate_ma(sbr, ratio_short)
    rs2 = calculate_ma(sbr, ratio_long)
    rs_ratio = 100 * ((rs1 - rs2) / rs2 + 1)
    
    # Momentum of the ratio
    rm1 = calculate_ma(rs_ratio, momentum_short)
    rm2 = calculate_ma(rs_ratio, momentum_long)
    rs_momentum = 100 * ((rm1 - rm2) / rm2 + 1)
    
    return rs_ratio, rs_momentum

def get_rrg_quadrant(rs_ratio, rs_momentum):
    """Determine RRG quadrant"""
    if pd.isna(rs_ratio) or pd.isna(rs_momentum):
        return None
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading"
    elif rs_ratio < 100 and rs_momentum >= 100:
        return "Improving"
    elif rs_ratio < 100 and rs_momentum < 100:
        return "Lagging"
    else:  # rs_ratio >= 100 and rs_momentum < 100
        return "Weakening"

# =============================================================================
# TRADE CLASS
# =============================================================================

class Trade:
    def __init__(self, symbol, entry_date, entry_price, size, atr):
        self.symbol = symbol
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.size = size
        self.atr = atr
        
        # TP at 10 ATR
        self.take_profit = entry_price + (10 * atr)
        
        # Trailing SL - starts at None (only quadrant exit initially)
        self.trailing_sl = None
        self.highest_atr_gain = 0
        
        # Exit tracking
        self.exit_date = None
        self.exit_price = None
        self.pnl = 0
        self.pnl_pct = 0
        self.holding_days = 0
        self.exit_reason = None

# =============================================================================
# BACKTEST ENGINE
# =============================================================================

def fetch_data(symbols, start_date, end_date):
    """Fetch OHLC data for all symbols"""
    all_symbols = list(symbols.keys()) + [BENCHMARK]
    print(f"Fetching data for {len(all_symbols)} symbols...")
    
    # Fetch in batches to avoid timeout
    batch_size = 50
    all_data = None
    
    for i in range(0, len(all_symbols), batch_size):
        batch = all_symbols[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}: {len(batch)} symbols...")
        try:
            data = yf.download(batch, start=start_date, end=end_date, progress=False, threads=True)
            if all_data is None:
                all_data = data
            else:
                # Merge data
                for col in data.columns.levels[0] if isinstance(data.columns, pd.MultiIndex) else []:
                    for sym in data.columns.get_level_values(1).unique() if isinstance(data.columns, pd.MultiIndex) else batch:
                        try:
                            all_data[(col, sym)] = data[(col, sym)]
                        except:
                            pass
        except Exception as e:
            print(f"  Error in batch: {e}")
    
    return all_data

def run_backtest(start_date='2020-01-01', end_date='2025-12-31'):
    print("=" * 70)
    print("RRG QUADRANT STRATEGY BACKTEST v2")
    print("=" * 70)
    print(f"Period: {start_date} to {end_date}")
    print(f"Universe: {len(HK_STOCKS)} HK stocks")
    print("\n📋 STRATEGY RULES:")
    print("-" * 40)
    print("ENTRY: Lagging → Improving/Leading for 2+ days, buy Day 3 open")
    print("       (if still not back in Lagging)")
    print("EXIT:  Falls back to Lagging quadrant")
    print("TP:    10 ATR")
    print("TRAIL: ≥4 ATR → breakeven")
    print("       ≥5 ATR → trail 1 ATR, ≥6 ATR → trail 2 ATR, etc.")
    print("=" * 70)
    
    # Fetch data
    data = fetch_data(HK_STOCKS, start_date, end_date)
    
    if data is None or data.empty:
        print("ERROR: No data fetched")
        return None
    
    # Extract OHLC
    try:
        close_data = data['Close']
        high_data = data['High']
        low_data = data['Low']
        open_data = data['Open']
    except:
        print("ERROR: Cannot extract OHLC data")
        return None
    
    if BENCHMARK not in close_data.columns:
        print(f"ERROR: Benchmark {BENCHMARK} not found")
        return None
    
    benchmark_close = close_data[BENCHMARK]
    
    # Calculate RRG and ATR for all stocks
    print("\nCalculating RRG values and ATR...")
    rrg_data = {}
    atr_data = {}
    
    for symbol in HK_STOCKS.keys():
        if symbol not in close_data.columns:
            continue
        
        asset_close = close_data[symbol]
        asset_high = high_data[symbol]
        asset_low = low_data[symbol]
        
        # Skip if too many NaN
        if asset_close.isna().sum() > len(asset_close) * 0.5:
            continue
        
        rs_ratio, rs_momentum = calculate_rrg_values(asset_close, benchmark_close)
        
        quadrants = pd.Series(index=close_data.index, dtype=object)
        for i in range(len(close_data)):
            quadrants.iloc[i] = get_rrg_quadrant(rs_ratio.iloc[i], rs_momentum.iloc[i])
        
        rrg_data[symbol] = {
            'rs_ratio': rs_ratio,
            'rs_momentum': rs_momentum,
            'quadrant': quadrants
        }
        
        atr_data[symbol] = calculate_atr(asset_high, asset_low, asset_close)
    
    print(f"Calculated RRG for {len(rrg_data)} stocks")
    
    # Track emergence from Lagging
    # Key: symbol, Value: {'days_out': count, 'first_quadrant': quadrant}
    emergence_tracker = {}
    
    # Run simulation
    trades = []
    active_trades = {}
    capital = INITIAL_CAPITAL
    equity_curve = []
    
    dates = close_data.index.tolist()
    
    print("\nRunning simulation...")
    
    for i in range(30, len(dates) - 1):
        current_date = dates[i]
        next_date = dates[i + 1]
        
        # =====================================================================
        # 1. CHECK EXITS FOR ACTIVE TRADES
        # =====================================================================
        symbols_to_remove = []
        
        for symbol, trade in active_trades.items():
            if symbol not in close_data.columns:
                continue
            
            current_high = high_data[symbol].iloc[i]
            current_low = low_data[symbol].iloc[i]
            current_close = close_data[symbol].iloc[i]
            current_quadrant = rrg_data[symbol]['quadrant'].iloc[i]
            
            if pd.isna(current_close):
                continue
            
            trade.holding_days += 1
            exit_price = None
            exit_reason = None
            
            # Calculate current ATR gain
            current_gain = current_high - trade.entry_price
            current_atr_gain = current_gain / trade.atr if trade.atr > 0 else 0
            
            # Update highest ATR gain
            if current_atr_gain > trade.highest_atr_gain:
                trade.highest_atr_gain = current_atr_gain
            
            # Update trailing SL based on ATR gain thresholds
            if trade.highest_atr_gain >= 9:
                # Trail 5 ATR below entry (lock in 4 ATR profit minimum)
                new_sl = trade.entry_price + (4 * trade.atr)
                if trade.trailing_sl is None or new_sl > trade.trailing_sl:
                    trade.trailing_sl = new_sl
            elif trade.highest_atr_gain >= 8:
                # Trail 4 ATR below entry (lock in 3 ATR profit)
                new_sl = trade.entry_price + (3 * trade.atr)
                if trade.trailing_sl is None or new_sl > trade.trailing_sl:
                    trade.trailing_sl = new_sl
            elif trade.highest_atr_gain >= 7:
                # Trail 3 ATR below entry (lock in 2 ATR profit)
                new_sl = trade.entry_price + (2 * trade.atr)
                if trade.trailing_sl is None or new_sl > trade.trailing_sl:
                    trade.trailing_sl = new_sl
            elif trade.highest_atr_gain >= 6:
                # Trail 2 ATR below entry (lock in 1 ATR profit)
                new_sl = trade.entry_price + (1 * trade.atr)
                if trade.trailing_sl is None or new_sl > trade.trailing_sl:
                    trade.trailing_sl = new_sl
            elif trade.highest_atr_gain >= 5:
                # Trail 1 ATR below entry (breakeven + small profit)
                new_sl = trade.entry_price + (0 * trade.atr)  # ~breakeven
                if trade.trailing_sl is None or new_sl > trade.trailing_sl:
                    trade.trailing_sl = new_sl
            elif trade.highest_atr_gain >= 4:
                # Move to breakeven
                new_sl = trade.entry_price
                if trade.trailing_sl is None or new_sl > trade.trailing_sl:
                    trade.trailing_sl = new_sl
            
            # Check TP at 10 ATR
            if current_high >= trade.take_profit:
                exit_price = trade.take_profit
                exit_reason = "Take Profit (10 ATR)"
            
            # Check trailing SL
            if exit_price is None and trade.trailing_sl is not None:
                if current_low <= trade.trailing_sl:
                    exit_price = trade.trailing_sl
                    exit_reason = f"Trailing SL ({trade.highest_atr_gain:.1f} ATR peak)"
            
            # Check quadrant exit - falls back to Lagging
            if exit_price is None and current_quadrant == "Lagging":
                exit_price = current_close
                exit_reason = "Quadrant Exit (Lagging)"
            
            # Process exit
            if exit_price is not None:
                pnl = trade.size * (exit_price - trade.entry_price)
                pnl -= trade.size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                pnl -= trade.size * exit_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                
                trade.pnl = pnl
                trade.exit_price = exit_price
                trade.exit_date = current_date
                trade.exit_reason = exit_reason
                trade.pnl_pct = pnl / (trade.size * trade.entry_price) * 100
                
                capital += trade.size * exit_price  # Return position value
                capital += pnl  # Add/subtract P&L
                capital -= trade.size * exit_price  # Subtract to avoid double counting
                capital += pnl  # The actual P&L
                
                # Simpler: just add pnl and return position
                capital = capital  # Already handled via pnl
                
                trades.append(trade)
                symbols_to_remove.append(symbol)
        
        for symbol in symbols_to_remove:
            del active_trades[symbol]
        
        # =====================================================================
        # 2. TRACK EMERGENCE FROM LAGGING
        # =====================================================================
        for symbol in rrg_data.keys():
            if symbol in active_trades:
                continue
            
            current_quadrant = rrg_data[symbol]['quadrant'].iloc[i]
            prev_quadrant = rrg_data[symbol]['quadrant'].iloc[i-1] if i > 0 else None
            
            if current_quadrant is None:
                continue
            
            # If currently in Lagging, reset tracker
            if current_quadrant == "Lagging":
                if symbol in emergence_tracker:
                    del emergence_tracker[symbol]
                continue
            
            # If was in Lagging yesterday and now in Improving/Leading
            if prev_quadrant == "Lagging" and current_quadrant in ["Improving", "Leading"]:
                emergence_tracker[symbol] = {
                    'days_out': 1,
                    'first_quadrant': current_quadrant,
                    'emergence_date': current_date
                }
            # If already tracking and still not Lagging
            elif symbol in emergence_tracker and current_quadrant in ["Improving", "Leading", "Weakening"]:
                emergence_tracker[symbol]['days_out'] += 1
            # If fell back to Lagging while tracking
            elif symbol in emergence_tracker and current_quadrant == "Lagging":
                del emergence_tracker[symbol]
        
        # =====================================================================
        # 3. CHECK FOR NEW ENTRIES (Day 3 after emergence)
        # =====================================================================
        for symbol, tracker in list(emergence_tracker.items()):
            if symbol in active_trades:
                continue
            if symbol not in close_data.columns:
                continue
            
            # Buy on Day 3 if still not in Lagging
            if tracker['days_out'] >= 2:  # 2 days means we're at day 3
                current_quadrant = rrg_data[symbol]['quadrant'].iloc[i]
                
                # Skip if back in Lagging
                if current_quadrant == "Lagging":
                    del emergence_tracker[symbol]
                    continue
                
                # Get entry price (next day open)
                entry_price = open_data[symbol].iloc[i + 1] if i + 1 < len(dates) else None
                
                if entry_price is None or pd.isna(entry_price) or entry_price <= 0:
                    continue
                
                # Get ATR
                atr = atr_data[symbol].iloc[i] if symbol in atr_data else None
                if atr is None or pd.isna(atr) or atr <= 0:
                    atr = entry_price * 0.03  # Fallback: 3% of price
                
                # Calculate position size
                position_value = capital * POSITION_SIZE
                size = position_value / entry_price
                
                if size <= 0:
                    continue
                
                # Create trade
                trade = Trade(
                    symbol=symbol,
                    entry_date=next_date,
                    entry_price=entry_price,
                    size=size,
                    atr=atr
                )
                
                # Deduct entry costs
                entry_cost = size * entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                capital -= entry_cost
                
                active_trades[symbol] = trade
                
                # Remove from tracker (trade placed)
                del emergence_tracker[symbol]
        
        # =====================================================================
        # 4. TRACK EQUITY
        # =====================================================================
        unrealized = 0
        for symbol, trade in active_trades.items():
            if symbol in close_data.columns:
                current_price = close_data[symbol].iloc[i]
                if not pd.isna(current_price):
                    unrealized += trade.size * (current_price - trade.entry_price)
        
        equity_curve.append({
            'date': current_date,
            'capital': capital,
            'unrealized': unrealized,
            'equity': capital + unrealized,
            'active_positions': len(active_trades)
        })
    
    # =========================================================================
    # CLOSE REMAINING TRADES AT END
    # =========================================================================
    for symbol, trade in active_trades.items():
        if symbol in close_data.columns:
            exit_price = close_data[symbol].iloc[-1]
            if not pd.isna(exit_price):
                pnl = trade.size * (exit_price - trade.entry_price)
                pnl -= trade.size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                pnl -= trade.size * exit_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                
                trade.pnl = pnl
                trade.exit_price = exit_price
                trade.exit_date = dates[-1]
                trade.exit_reason = "End of Test"
                trade.pnl_pct = pnl / (trade.size * trade.entry_price) * 100
                
                capital += pnl
                trades.append(trade)
    
    print_results(trades, equity_curve)
    save_results(trades, equity_curve)
    
    return trades, equity_curve

def print_results(trades, equity_curve):
    """Print backtest results"""
    if not trades:
        print("\n❌ NO TRADES EXECUTED")
        return
    
    print("\n" + "=" * 70)
    print("📊 BACKTEST RESULTS")
    print("=" * 70)
    
    total_trades = len(trades)
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]
    
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    
    total_pnl = sum(t.pnl for t in trades)
    gross_profit = sum(t.pnl for t in winning_trades)
    gross_loss = abs(sum(t.pnl for t in losing_trades))
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
    avg_win_pct = np.mean([t.pnl_pct for t in winning_trades]) if winning_trades else 0
    avg_loss_pct = np.mean([t.pnl_pct for t in losing_trades]) if losing_trades else 0
    
    avg_holding = np.mean([t.holding_days for t in trades])
    
    print(f"\n📈 TRADE STATISTICS")
    print("-" * 40)
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {len(winning_trades)} ({win_rate:.1f}%)")
    print(f"Losing Trades: {len(losing_trades)}")
    print(f"Average Holding Days: {avg_holding:.1f}")
    
    print(f"\n💰 P&L ANALYSIS")
    print("-" * 40)
    print(f"Total P&L: ${total_pnl:,.0f}")
    print(f"Gross Profit: ${gross_profit:,.0f}")
    print(f"Gross Loss: ${gross_loss:,.0f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Avg Win: ${avg_win:,.0f} ({avg_win_pct:.1f}%)")
    print(f"Avg Loss: ${avg_loss:,.0f} ({avg_loss_pct:.1f}%)")
    
    # Best/Worst trades
    if trades:
        best_trade = max(trades, key=lambda t: t.pnl)
        worst_trade = min(trades, key=lambda t: t.pnl)
        print(f"\n🏆 Best Trade: {best_trade.symbol} +${best_trade.pnl:,.0f} ({best_trade.pnl_pct:.1f}%)")
        print(f"💀 Worst Trade: {worst_trade.symbol} ${worst_trade.pnl:,.0f} ({worst_trade.pnl_pct:.1f}%)")
    
    if equity_curve:
        equity_df = pd.DataFrame(equity_curve)
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
        
        if len(equity_df) > 1:
            daily_returns = equity_df['returns'].dropna()
            
            equity_df['peak'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
            max_dd = abs(equity_df['drawdown'].min()) * 100
            
            # Find max DD period
            dd_end_idx = equity_df['drawdown'].idxmin()
            dd_start_idx = equity_df.loc[:dd_end_idx, 'equity'].idxmax()
            
            mean_return = daily_returns.mean() * 252
            std_return = daily_returns.std() * np.sqrt(252)
            sharpe = mean_return / std_return if std_return > 0 else 0
            
            downside_returns = daily_returns[daily_returns < 0]
            downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino = mean_return / downside_std if downside_std > 0 else 0
            
            years = len(equity_df) / 252
            cagr = ((final_equity / INITIAL_CAPITAL) ** (1/years) - 1) * 100 if years > 0 else 0
            calmar = cagr / max_dd if max_dd > 0 else 0
            
            print(f"\n📊 RISK METRICS")
            print("-" * 40)
            print(f"Initial Capital: ${INITIAL_CAPITAL:,.0f}")
            print(f"Final Equity: ${final_equity:,.0f}")
            print(f"Total Return: {total_return:.2f}%")
            print(f"CAGR: {cagr:.2f}%")
            print(f"Max Drawdown: {max_dd:.2f}%")
            print(f"Sharpe Ratio: {sharpe:.2f}")
            print(f"Sortino Ratio: {sortino:.2f}")
            print(f"Calmar Ratio: {calmar:.2f}")
    
    print(f"\n🚪 EXIT REASONS")
    print("-" * 40)
    exit_reasons = {}
    for t in trades:
        reason = t.exit_reason or "Unknown"
        # Simplify trailing SL reasons
        if "Trailing SL" in reason:
            reason = "Trailing SL"
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        pct = count / total_trades * 100
        avg_pnl = np.mean([t.pnl for t in trades if (t.exit_reason or "").startswith(reason.split()[0])])
        print(f"{reason}: {count} ({pct:.1f}%) avg ${avg_pnl:,.0f}")

def save_results(trades, equity_curve):
    """Save results to CSV"""
    if not trades:
        return
    
    # Save trades
    results = []
    for t in trades:
        results.append({
            'Symbol': t.symbol,
            'Entry Date': t.entry_date,
            'Entry Price': round(t.entry_price, 3),
            'Exit Date': t.exit_date,
            'Exit Price': round(t.exit_price, 3) if t.exit_price else None,
            'ATR': round(t.atr, 3),
            'Size': round(t.size, 0),
            'P&L': round(t.pnl, 0),
            'P&L %': round(t.pnl_pct, 2),
            'Holding Days': t.holding_days,
            'Peak ATR Gain': round(t.highest_atr_gain, 2),
            'Exit Reason': t.exit_reason
        })
    
    df = pd.DataFrame(results)
    trades_path = '/root/clawd/rrg_quadrant_results.csv'
    df.to_csv(trades_path, index=False)
    print(f"\n📁 Trade results saved to: {trades_path}")
    
    # Save equity curve
    if equity_curve:
        eq_df = pd.DataFrame(equity_curve)
        eq_path = '/root/clawd/rrg_quadrant_equity.csv'
        eq_df.to_csv(eq_path, index=False)
        print(f"📁 Equity curve saved to: {eq_path}")

if __name__ == '__main__':
    import sys
    start = sys.argv[1] if len(sys.argv) > 1 else '2020-01-01'
    end = sys.argv[2] if len(sys.argv) > 2 else '2025-12-31'
    trades, equity = run_backtest(start, end)
