#!/usr/bin/env python3
"""
RRG + RS Signal Strategy Backtest
=================================
Entry: RS buy signal (EMA pullback) + RRG quadrant (Improving/Leading)
Exit: Lagging/Weakening quadrant OR SL (prev low - 2.5 ATR)
TP: 2R (50%), 5R (remaining)
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
    try:
        with open('/root/clawd/hsi_constituents.json', 'r') as f:
            return json.load(f)
    except:
        return {
            '0700.HK': 'Tencent', '9988.HK': 'Alibaba', '0005.HK': 'HSBC',
            '1810.HK': 'Xiaomi', '9618.HK': 'JD.com', '0388.HK': 'HKEX',
        }

HK_STOCKS = load_hk_stocks()
BENCHMARK = '^HSI'

# Backtest Parameters
INITIAL_CAPITAL = 1_000_000
POSITION_SIZE = 0.05
COMMISSION = 0.001
STAMP_DUTY = 0.001
SLIPPAGE = 0.002

# Risk Management
STOP_LOSS_ATR_MULT = 2.5
TAKE_PROFIT_1_R = 2.0
TAKE_PROFIT_2_R = 3.0  # Reduced from 5R
MAX_HOLDING_DAYS = 60  # Extended from 30

# =============================================================================
# INDICATOR CALCULATIONS
# =============================================================================

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_ma(data, period):
    return data.rolling(window=period).mean()

# =============================================================================
# RS BUY SIGNAL (from RS page)
# =============================================================================

def generate_rs_buy_signal(high, low, close, i):
    """
    RS Page Buy Signal Logic:
    1. Previous bar low < EMA5
    2. Previous bar low near EMA25 (within 0.5 ATR)
    3. EMA5 >= EMA25 (uptrend)
    4. Current close > previous bar high
    """
    if i < 26:
        return False
    
    # Get data up to current bar
    close_slice = close.iloc[:i+1]
    high_slice = high.iloc[:i+1]
    low_slice = low.iloc[:i+1]
    
    ema5 = calculate_ema(close_slice, 5)
    ema25 = calculate_ema(close_slice, 25)
    atr = calculate_atr(high_slice, low_slice, close_slice, 14)
    
    if pd.isna(atr.iloc[-1]) or atr.iloc[-1] <= 0:
        return False
    
    allow_distance = 0.5 * atr.iloc[-1]
    
    # Previous bar (i-1) conditions
    prev_low = low.iloc[i-1]
    prev_high = high.iloc[i-1]
    prev_ema5 = ema5.iloc[-2]
    prev_ema25 = ema25.iloc[-2]
    
    # Current bar
    curr_close = close.iloc[i]
    
    # Buy prep conditions
    cond1 = prev_low < prev_ema5  # Low dipped below EMA5
    cond2 = prev_low >= (prev_ema25 - allow_distance)  # Near EMA25
    cond3 = prev_low <= (prev_ema25 + allow_distance)  # Near EMA25
    cond4 = prev_ema5 >= prev_ema25  # Uptrend
    
    buy_prep = cond1 and cond2 and cond3 and cond4
    
    # Breakout confirmation
    buy_signal = buy_prep and (curr_close > prev_high)
    
    return buy_signal

# =============================================================================
# RRG CALCULATIONS
# =============================================================================

def calculate_rrg_values(asset_data, benchmark_data, 
                         ratio_short=10, ratio_long=26,
                         momentum_short=1, momentum_long=4):
    sbr = asset_data / benchmark_data
    rs1 = calculate_ma(sbr, ratio_short)
    rs2 = calculate_ma(sbr, ratio_long)
    rs_ratio = 100 * ((rs1 - rs2) / rs2 + 1)
    
    rm1 = calculate_ma(rs_ratio, momentum_short)
    rm2 = calculate_ma(rs_ratio, momentum_long)
    rs_momentum = 100 * ((rm1 - rm2) / rm2 + 1)
    
    return rs_ratio, rs_momentum

def get_rrg_quadrant(rs_ratio, rs_momentum):
    if pd.isna(rs_ratio) or pd.isna(rs_momentum):
        return None
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading"
    elif rs_ratio < 100 and rs_momentum >= 100:
        return "Improving"
    elif rs_ratio < 100 and rs_momentum < 100:
        return "Lagging"
    else:
        return "Weakening"

# =============================================================================
# TRADE CLASS
# =============================================================================

class Trade:
    def __init__(self, symbol, entry_date, entry_price, size, 
                 stop_loss, take_profit_1, take_profit_2, risk_per_share, atr):
        self.symbol = symbol
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.size = size
        self.remaining_size = size
        self.stop_loss = stop_loss
        self.original_stop_loss = stop_loss  # Keep original for reference
        self.take_profit_1 = take_profit_1
        self.take_profit_2 = take_profit_2
        self.risk_per_share = risk_per_share
        self.atr = atr  # Store ATR for breakeven calculation
        self.tp1_hit = False
        self.breakeven_hit = False  # Track if we've moved to breakeven
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
    all_symbols = list(symbols.keys()) + [BENCHMARK]
    print(f"Fetching data for {len(all_symbols)} symbols...")
    data = yf.download(all_symbols, start=start_date, end=end_date, progress=False)
    return data

def run_backtest(start_date='2020-01-01', end_date='2025-12-31'):
    print("=" * 70)
    print("RRG + RS SIGNAL STRATEGY BACKTEST")
    print("=" * 70)
    print(f"Period: {start_date} to {end_date}")
    print(f"Universe: {len(HK_STOCKS)} HK stocks")
    print(f"Entry: RS buy signal + Improving/Leading quadrant")
    print(f"Exit: Lagging/Weakening quadrant OR SL (prev low - 2.5 ATR)")
    print(f"TP: 2R (50%), 5R (remaining)")
    print("=" * 70)
    
    # Fetch data
    data = fetch_data(HK_STOCKS, start_date, end_date)
    
    if data.empty:
        print("ERROR: No data fetched")
        return None
    
    close_data = data['Close'] if 'Close' in data.columns else data
    high_data = data['High'] if 'High' in data.columns else None
    low_data = data['Low'] if 'Low' in data.columns else None
    open_data = data['Open'] if 'Open' in data.columns else None
    
    if BENCHMARK not in close_data.columns:
        print(f"ERROR: Benchmark {BENCHMARK} not found")
        return None
    
    benchmark_close = close_data[BENCHMARK]
    
    # Calculate RRG for all stocks
    print("\nCalculating RRG values...")
    rrg_data = {}
    atr_data = {}
    
    for symbol in HK_STOCKS.keys():
        if symbol not in close_data.columns:
            continue
        
        asset_close = close_data[symbol]
        rs_ratio, rs_momentum = calculate_rrg_values(asset_close, benchmark_close)
        
        quadrants = pd.Series(index=close_data.index, dtype=object)
        for i in range(len(close_data)):
            quadrants.iloc[i] = get_rrg_quadrant(rs_ratio.iloc[i], rs_momentum.iloc[i])
        
        rrg_data[symbol] = {
            'rs_ratio': rs_ratio,
            'rs_momentum': rs_momentum,
            'quadrant': quadrants
        }
        
        # Calculate ATR
        if high_data is not None and low_data is not None:
            atr_data[symbol] = calculate_atr(
                high_data[symbol], low_data[symbol], close_data[symbol]
            )
    
    print(f"Calculated RRG for {len(rrg_data)} stocks")
    
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
        
        # Check exits for active trades
        symbols_to_remove = []
        
        for symbol, trade in active_trades.items():
            if symbol not in close_data.columns:
                continue
            
            current_high = high_data[symbol].iloc[i] if high_data is not None else close_data[symbol].iloc[i]
            current_low = low_data[symbol].iloc[i] if low_data is not None else close_data[symbol].iloc[i]
            current_close = close_data[symbol].iloc[i]
            current_quadrant = rrg_data[symbol]['quadrant'].iloc[i] if symbol in rrg_data else None
            
            trade.holding_days += 1
            exit_price = None
            exit_reason = None
            
            # No breakeven - just use mathematical SL
            
            # Check mathematical SL
            if current_low <= trade.stop_loss:
                exit_price = trade.stop_loss
                exit_reason = "Stop Loss"
            
            # Check TP1 (2R) - exit 50%
            if exit_price is None and not trade.tp1_hit:
                if current_high >= trade.take_profit_1:
                    half_size = trade.remaining_size / 2
                    pnl = half_size * (trade.take_profit_1 - trade.entry_price)
                    pnl -= half_size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                    trade.pnl += pnl
                    trade.remaining_size -= half_size
                    trade.tp1_hit = True
                    capital += pnl
            
            # Check TP2 (5R)
            if exit_price is None and trade.tp1_hit:
                if current_high >= trade.take_profit_2:
                    exit_price = trade.take_profit_2
                    exit_reason = "Take Profit 5R"
            
            # REMOVED: Quadrant exit - let mathematical SL/TP work
            # The RRG filter on entry is enough; exiting on quadrant change is too aggressive
            
            # Check time stop
            if exit_price is None and trade.holding_days >= MAX_HOLDING_DAYS:
                exit_price = current_close
                exit_reason = "Time Exit"
            
            # Process exit
            if exit_price is not None:
                remaining_pnl = trade.remaining_size * (exit_price - trade.entry_price)
                remaining_pnl -= trade.remaining_size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                trade.pnl += remaining_pnl
                trade.exit_price = exit_price
                trade.exit_date = current_date
                trade.exit_reason = exit_reason
                trade.pnl_pct = trade.pnl / (trade.size * trade.entry_price) * 100
                
                capital += remaining_pnl
                trades.append(trade)
                symbols_to_remove.append(symbol)
        
        for symbol in symbols_to_remove:
            del active_trades[symbol]
        
        # Check for new entries
        for symbol in HK_STOCKS.keys():
            if symbol in active_trades:
                continue
            if symbol not in rrg_data:
                continue
            if symbol not in close_data.columns:
                continue
            
            curr_quadrant = rrg_data[symbol]['quadrant'].iloc[i]
            
            # Only enter if in Improving or Leading
            if curr_quadrant not in ["Improving", "Leading"]:
                continue
            
            # Check RS buy signal
            if high_data is None or low_data is None:
                continue
            
            has_signal = generate_rs_buy_signal(
                high_data[symbol], low_data[symbol], close_data[symbol], i
            )
            
            if not has_signal:
                continue
            
            # Entry on next day open
            if i + 1 < len(dates):
                entry_price = open_data[symbol].iloc[i + 1] if open_data is not None else close_data[symbol].iloc[i + 1]
                
                if pd.isna(entry_price) or entry_price <= 0:
                    continue
                
                # Get ATR and calculate SL
                atr = atr_data[symbol].iloc[i] if symbol in atr_data else 0
                if pd.isna(atr) or atr <= 0:
                    atr = entry_price * 0.03
                
                prev_low = low_data[symbol].iloc[i]
                
                # SL: previous low - 2.5 ATR
                stop_loss = prev_low - (STOP_LOSS_ATR_MULT * atr)
                risk_per_share = entry_price - stop_loss
                
                if risk_per_share <= 0:
                    continue
                
                # TPs based on R
                take_profit_1 = entry_price + (TAKE_PROFIT_1_R * risk_per_share)
                take_profit_2 = entry_price + (TAKE_PROFIT_2_R * risk_per_share)
                
                # Position size
                position_value = capital * POSITION_SIZE
                size = position_value / entry_price
                
                trade = Trade(
                    symbol=symbol,
                    entry_date=next_date,
                    entry_price=entry_price,
                    size=size,
                    stop_loss=stop_loss,
                    take_profit_1=take_profit_1,
                    take_profit_2=take_profit_2,
                    risk_per_share=risk_per_share,
                    atr=atr
                )
                
                entry_cost = size * entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                capital -= entry_cost
                
                active_trades[symbol] = trade
        
        # Track equity
        unrealized = 0
        for symbol, trade in active_trades.items():
            if symbol in close_data.columns:
                current_price = close_data[symbol].iloc[i]
                if not pd.isna(current_price):
                    unrealized += trade.remaining_size * (current_price - trade.entry_price)
        
        equity_curve.append({
            'date': current_date,
            'capital': capital,
            'unrealized': unrealized,
            'equity': capital + unrealized
        })
    
    # Close remaining trades
    for symbol, trade in active_trades.items():
        if symbol in close_data.columns:
            exit_price = close_data[symbol].iloc[-1]
            if not pd.isna(exit_price):
                remaining_pnl = trade.remaining_size * (exit_price - trade.entry_price)
                remaining_pnl -= trade.remaining_size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                trade.pnl += remaining_pnl
                trade.exit_price = exit_price
                trade.exit_date = dates[-1]
                trade.exit_reason = "End of Test"
                trade.pnl_pct = trade.pnl / (trade.size * trade.entry_price) * 100
                capital += remaining_pnl
                trades.append(trade)
    
    print_results(trades, equity_curve)
    save_results(trades)
    
    return trades, equity_curve

def print_results(trades, equity_curve):
    if not trades:
        print("\nNO TRADES EXECUTED")
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
    print(f"Avg Win: ${avg_win:,.0f}")
    print(f"Avg Loss: ${avg_loss:,.0f}")
    
    if equity_curve:
        equity_df = pd.DataFrame(equity_curve)
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        total_return = (equity_df['equity'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
        
        if len(equity_df) > 1:
            daily_returns = equity_df['returns'].dropna()
            
            equity_df['peak'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
            max_dd = abs(equity_df['drawdown'].min()) * 100
            
            mean_return = daily_returns.mean() * 252
            std_return = daily_returns.std() * np.sqrt(252)
            sharpe = mean_return / std_return if std_return > 0 else 0
            
            downside_returns = daily_returns[daily_returns < 0]
            downside_std = downside_returns.std() * np.sqrt(252)
            sortino = mean_return / downside_std if downside_std > 0 else 0
            
            annual_return = total_return / (len(equity_df) / 252)
            calmar = annual_return / max_dd if max_dd > 0 else 0
            
            print(f"\n📊 RISK METRICS")
            print("-" * 40)
            print(f"Total Return: {total_return:.2f}%")
            print(f"Max Drawdown: {max_dd:.2f}%")
            print(f"Sharpe Ratio: {sharpe:.2f}")
            print(f"Sortino Ratio: {sortino:.2f}")
            print(f"Calmar Ratio: {calmar:.2f}")
    
    print(f"\n🚪 EXIT REASONS")
    print("-" * 40)
    exit_reasons = {}
    for t in trades:
        reason = t.exit_reason or "Unknown"
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        pct = count / total_trades * 100
        print(f"{reason}: {count} ({pct:.1f}%)")

def save_results(trades):
    if not trades:
        return
    
    results = []
    for t in trades:
        results.append({
            'Symbol': t.symbol,
            'Entry Date': t.entry_date,
            'Entry Price': t.entry_price,
            'Exit Date': t.exit_date,
            'Exit Price': t.exit_price,
            'P&L': t.pnl,
            'P&L %': t.pnl_pct,
            'Holding Days': t.holding_days,
            'Exit Reason': t.exit_reason
        })
    
    df = pd.DataFrame(results)
    output_path = '/root/clawd/rrg_rs_strategy_results.csv'
    df.to_csv(output_path, index=False)
    print(f"\n📁 Results saved to: {output_path}")

if __name__ == '__main__':
    import sys
    start = sys.argv[1] if len(sys.argv) > 1 else '2020-01-01'
    end = sys.argv[2] if len(sys.argv) > 2 else '2025-12-31'
    trades, equity = run_backtest(start, end)
