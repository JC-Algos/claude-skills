#!/usr/bin/env python3
"""
RRG Quadrant Rotation Strategy Backtest
========================================
Entry: Improving→Leading or Weakening→Leading transition
Exit: 2R (50%), 5R (remaining) or quadrant exit from Leading
SL: Previous day low - 2.5 ATR (long) / high + 2.5 ATR (short)
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

# Load HK stocks
def load_hk_stocks():
    try:
        with open('/root/clawd/hsi_constituents.json', 'r') as f:
            return json.load(f)
    except:
        # Fallback to common HK stocks
        return {
            '0700.HK': 'Tencent', '9988.HK': 'Alibaba', '0005.HK': 'HSBC',
            '1810.HK': 'Xiaomi', '9618.HK': 'JD.com', '0388.HK': 'HKEX',
            '0941.HK': 'ChinaMobile', '2318.HK': 'PingAn', '0001.HK': 'CKH',
            '0016.HK': 'SHK Properties'
        }

HK_STOCKS = load_hk_stocks()
BENCHMARK = '^HSI'

# Backtest Parameters
INITIAL_CAPITAL = 1_000_000  # HKD
POSITION_SIZE = 0.05  # 5% per trade
COMMISSION = 0.001  # 0.1%
STAMP_DUTY = 0.001  # 0.1%
SLIPPAGE = 0.002  # 0.2%

# Risk Management
STOP_LOSS_ATR_MULT = 2.5  # SL at prev low - 2.5 ATR
TAKE_PROFIT_1_R = 2.0  # First TP: 50% at 2R
TAKE_PROFIT_2_R = 5.0  # Second TP: remaining at 5R
MAX_HOLDING_DAYS = 30  # Time stop

# =============================================================================
# RRG CALCULATIONS (Daily-adapted)
# =============================================================================

def calculate_ma(data, period):
    """Calculate moving average"""
    return data.rolling(window=period).mean()

def calculate_rrg_values_daily(asset_data, benchmark_data, 
                                 ratio_short=10, ratio_long=26,
                                 momentum_short=1, momentum_long=4):
    """
    Calculate RS-Ratio and RS-Momentum for RRG (daily version)
    Shorter periods for daily data: 10/26 for ratio, 1/4 for momentum
    """
    # Strength-based ratio
    sbr = asset_data / benchmark_data
    
    # RS-Ratio: Normalized ratio of short vs long MA
    rs1 = calculate_ma(sbr, ratio_short)
    rs2 = calculate_ma(sbr, ratio_long)
    rs_ratio = 100 * ((rs1 - rs2) / rs2 + 1)
    
    # RS-Momentum: Rate of change of RS-Ratio
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
# INDICATOR CALCULATIONS
# =============================================================================

def calculate_atr(df, period=14):
    """Calculate ATR"""
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(period).mean()
    return df['ATR']

# =============================================================================
# TRADE CLASS
# =============================================================================

class Trade:
    def __init__(self, symbol, entry_date, entry_price, direction, size, 
                 stop_loss, take_profit_1, take_profit_2, prev_low, prev_high):
        self.symbol = symbol
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.direction = direction  # 1 (long) or -1 (short)
        self.size = size
        self.remaining_size = size
        self.stop_loss = stop_loss
        self.take_profit_1 = take_profit_1  # 2R
        self.take_profit_2 = take_profit_2  # 5R
        self.prev_low = prev_low
        self.prev_high = prev_high
        self.tp1_hit = False
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
    """Fetch price data for all symbols"""
    all_symbols = list(symbols.keys()) + [BENCHMARK]
    
    print(f"Fetching data for {len(all_symbols)} symbols...")
    data = yf.download(all_symbols, start=start_date, end=end_date, progress=False)
    
    return data

def run_backtest(start_date='2020-01-01', end_date='2025-12-31'):
    """Run full backtest"""
    
    print("=" * 70)
    print("RRG QUADRANT ROTATION STRATEGY BACKTEST")
    print("=" * 70)
    print(f"Period: {start_date} to {end_date}")
    print(f"Universe: {len(HK_STOCKS)} HK stocks vs HSI benchmark")
    print(f"Entry: Improving→Leading or Weakening→Leading")
    print(f"Exit: 2R (50%), 5R (50%) or quadrant change from Leading")
    print(f"SL: Prev Low - 2.5 ATR (Long) / Prev High + 2.5 ATR (Short)")
    print("=" * 70)
    
    # Fetch all data
    data = fetch_data(HK_STOCKS, start_date, end_date)
    
    if data.empty:
        print("ERROR: No data fetched")
        return None
    
    # Extract OHLC for each symbol
    close_data = data['Close'] if 'Close' in data.columns else data
    high_data = data['High'] if 'High' in data.columns else None
    low_data = data['Low'] if 'Low' in data.columns else None
    open_data = data['Open'] if 'Open' in data.columns else None
    
    # Get benchmark data
    if BENCHMARK not in close_data.columns:
        print(f"ERROR: Benchmark {BENCHMARK} not found")
        return None
    
    benchmark_close = close_data[BENCHMARK]
    
    # Calculate RRG values for all stocks
    print("\nCalculating RRG values for all stocks...")
    rrg_data = {}
    atr_data = {}
    
    for symbol in HK_STOCKS.keys():
        if symbol not in close_data.columns:
            continue
        
        asset_close = close_data[symbol]
        rs_ratio, rs_momentum = calculate_rrg_values_daily(asset_close, benchmark_close)
        
        # Store quadrants for each day
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
            df_temp = pd.DataFrame({
                'High': high_data[symbol],
                'Low': low_data[symbol],
                'Close': close_data[symbol]
            })
            atr_data[symbol] = calculate_atr(df_temp)
    
    print(f"Calculated RRG for {len(rrg_data)} stocks")
    
    # Run simulation
    trades = []
    active_trades = {}  # symbol -> Trade
    capital = INITIAL_CAPITAL
    equity_curve = []
    
    dates = close_data.index.tolist()
    
    print("\nRunning simulation...")
    
    for i in range(30, len(dates) - 1):  # Need lookback and next day
        current_date = dates[i]
        next_date = dates[i + 1]
        prev_date = dates[i - 1]
        
        current_equity = capital
        
        # First: Check exits for active trades
        symbols_to_remove = []
        
        for symbol, trade in active_trades.items():
            if symbol not in close_data.columns or symbol not in open_data.columns:
                continue
            
            current_high = high_data[symbol].iloc[i] if high_data is not None else close_data[symbol].iloc[i]
            current_low = low_data[symbol].iloc[i] if low_data is not None else close_data[symbol].iloc[i]
            current_close = close_data[symbol].iloc[i]
            current_quadrant = rrg_data[symbol]['quadrant'].iloc[i] if symbol in rrg_data else None
            
            trade.holding_days += 1
            exit_price = None
            exit_reason = None
            
            # Check stop loss
            if trade.direction == 1:  # Long
                if current_low <= trade.stop_loss:
                    exit_price = trade.stop_loss
                    exit_reason = "Stop Loss"
            else:  # Short
                if current_high >= trade.stop_loss:
                    exit_price = trade.stop_loss
                    exit_reason = "Stop Loss"
            
            # Check TP1 (2R) - exit 50%
            if exit_price is None and not trade.tp1_hit:
                if trade.direction == 1:  # Long
                    if current_high >= trade.take_profit_1:
                        # Partial exit at TP1
                        half_size = trade.remaining_size / 2
                        pnl = half_size * (trade.take_profit_1 - trade.entry_price) * trade.direction
                        pnl -= half_size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                        trade.pnl += pnl
                        trade.remaining_size -= half_size
                        trade.tp1_hit = True
                        capital += pnl
                else:  # Short
                    if current_low <= trade.take_profit_1:
                        half_size = trade.remaining_size / 2
                        pnl = half_size * (trade.entry_price - trade.take_profit_1)
                        pnl -= half_size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                        trade.pnl += pnl
                        trade.remaining_size -= half_size
                        trade.tp1_hit = True
                        capital += pnl
            
            # Check TP2 (5R) - exit remaining
            if exit_price is None and trade.tp1_hit:
                if trade.direction == 1:  # Long
                    if current_high >= trade.take_profit_2:
                        exit_price = trade.take_profit_2
                        exit_reason = "Take Profit 5R"
                else:  # Short
                    if current_low <= trade.take_profit_2:
                        exit_price = trade.take_profit_2
                        exit_reason = "Take Profit 5R"
            
            # Check quadrant exit (no longer Leading)
            if exit_price is None and current_quadrant and current_quadrant != "Leading":
                exit_price = current_close
                exit_reason = f"Quadrant Exit ({current_quadrant})"
            
            # Check time stop
            if exit_price is None and trade.holding_days >= MAX_HOLDING_DAYS:
                exit_price = current_close
                exit_reason = "Time Exit"
            
            # Process exit
            if exit_price is not None:
                remaining_pnl = trade.remaining_size * (exit_price - trade.entry_price) * trade.direction
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
        
        # Check for new entries (signal today → enter tomorrow open)
        for symbol in HK_STOCKS.keys():
            if symbol in active_trades:
                continue
            if symbol not in rrg_data:
                continue
            if symbol not in close_data.columns:
                continue
            
            prev_quadrant = rrg_data[symbol]['quadrant'].iloc[i - 1]
            curr_quadrant = rrg_data[symbol]['quadrant'].iloc[i]
            
            # Entry signal: Improving→Leading or Weakening→Leading
            if curr_quadrant == "Leading" and prev_quadrant in ["Improving", "Weakening"]:
                # Calculate entry price (next day open)
                if i + 1 < len(dates):
                    entry_price = open_data[symbol].iloc[i + 1] if open_data is not None else close_data[symbol].iloc[i + 1]
                    
                    if pd.isna(entry_price) or entry_price <= 0:
                        continue
                    
                    # Get ATR and prev low/high
                    atr = atr_data[symbol].iloc[i] if symbol in atr_data else 0
                    if pd.isna(atr) or atr <= 0:
                        atr = entry_price * 0.03  # Fallback: 3% of price
                    
                    prev_low = low_data[symbol].iloc[i] if low_data is not None else close_data[symbol].iloc[i] * 0.98
                    prev_high = high_data[symbol].iloc[i] if high_data is not None else close_data[symbol].iloc[i] * 1.02
                    
                    # Direction: Long for Improving→Leading, Short for Weakening→Leading
                    if prev_quadrant == "Improving":
                        direction = 1  # Long - momentum improving
                    else:  # Weakening→Leading
                        direction = 1  # Also long - bouncing back to leading
                    
                    # Calculate position size
                    position_value = capital * POSITION_SIZE
                    size = position_value / entry_price
                    
                    # Risk per share (for R calculation)
                    if direction == 1:  # Long
                        stop_loss = prev_low - (STOP_LOSS_ATR_MULT * atr)
                        risk_per_share = entry_price - stop_loss
                        take_profit_1 = entry_price + (TAKE_PROFIT_1_R * risk_per_share)
                        take_profit_2 = entry_price + (TAKE_PROFIT_2_R * risk_per_share)
                    else:  # Short
                        stop_loss = prev_high + (STOP_LOSS_ATR_MULT * atr)
                        risk_per_share = stop_loss - entry_price
                        take_profit_1 = entry_price - (TAKE_PROFIT_1_R * risk_per_share)
                        take_profit_2 = entry_price - (TAKE_PROFIT_2_R * risk_per_share)
                    
                    trade = Trade(
                        symbol=symbol,
                        entry_date=next_date,
                        entry_price=entry_price,
                        direction=direction,
                        size=size,
                        stop_loss=stop_loss,
                        take_profit_1=take_profit_1,
                        take_profit_2=take_profit_2,
                        prev_low=prev_low,
                        prev_high=prev_high
                    )
                    
                    # Apply entry costs
                    entry_cost = size * entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                    capital -= entry_cost
                    
                    active_trades[symbol] = trade
        
        # Track equity
        unrealized = 0
        for symbol, trade in active_trades.items():
            if symbol in close_data.columns:
                current_price = close_data[symbol].iloc[i]
                if not pd.isna(current_price):
                    unrealized += trade.remaining_size * (current_price - trade.entry_price) * trade.direction
        
        equity_curve.append({
            'date': current_date,
            'capital': capital,
            'unrealized': unrealized,
            'equity': capital + unrealized
        })
    
    # Close remaining trades at last price
    for symbol, trade in active_trades.items():
        if symbol in close_data.columns:
            exit_price = close_data[symbol].iloc[-1]
            if not pd.isna(exit_price):
                remaining_pnl = trade.remaining_size * (exit_price - trade.entry_price) * trade.direction
                remaining_pnl -= trade.remaining_size * trade.entry_price * (COMMISSION + STAMP_DUTY + SLIPPAGE)
                trade.pnl += remaining_pnl
                trade.exit_price = exit_price
                trade.exit_date = dates[-1]
                trade.exit_reason = "End of Test"
                trade.pnl_pct = trade.pnl / (trade.size * trade.entry_price) * 100
                capital += remaining_pnl
                trades.append(trade)
    
    # Calculate metrics
    print_results(trades, equity_curve)
    
    # Save results
    save_results(trades)
    
    return trades, equity_curve

def print_results(trades, equity_curve):
    """Print backtest results"""
    if not trades:
        print("\nNO TRADES EXECUTED")
        return
    
    print("\n" + "=" * 70)
    print("📊 BACKTEST RESULTS")
    print("=" * 70)
    
    # Basic stats
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
    
    # Return stats
    if equity_curve:
        equity_df = pd.DataFrame(equity_curve)
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        total_return = (equity_df['equity'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
        
        # Risk metrics
        if len(equity_df) > 1:
            daily_returns = equity_df['returns'].dropna()
            
            # Max Drawdown
            equity_df['peak'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
            max_dd = abs(equity_df['drawdown'].min()) * 100
            
            # Sharpe (annualized)
            mean_return = daily_returns.mean() * 252
            std_return = daily_returns.std() * np.sqrt(252)
            sharpe = mean_return / std_return if std_return > 0 else 0
            
            # Sortino (annualized)
            downside_returns = daily_returns[daily_returns < 0]
            downside_std = downside_returns.std() * np.sqrt(252)
            sortino = mean_return / downside_std if downside_std > 0 else 0
            
            # Calmar
            annual_return = total_return / (len(equity_df) / 252)
            calmar = annual_return / max_dd if max_dd > 0 else 0
            
            print(f"\n📊 RISK METRICS")
            print("-" * 40)
            print(f"Total Return: {total_return:.2f}%")
            print(f"Max Drawdown: {max_dd:.2f}%")
            print(f"Sharpe Ratio: {sharpe:.2f}")
            print(f"Sortino Ratio: {sortino:.2f}")
            print(f"Calmar Ratio: {calmar:.2f}")
    
    # Exit reasons breakdown
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
    """Save trade results to CSV"""
    if not trades:
        return
    
    results = []
    for t in trades:
        results.append({
            'Symbol': t.symbol,
            'Entry Date': t.entry_date,
            'Entry Price': t.entry_price,
            'Direction': 'Long' if t.direction == 1 else 'Short',
            'Exit Date': t.exit_date,
            'Exit Price': t.exit_price,
            'P&L': t.pnl,
            'P&L %': t.pnl_pct,
            'Holding Days': t.holding_days,
            'Exit Reason': t.exit_reason
        })
    
    df = pd.DataFrame(results)
    output_path = '/root/clawd/rrg_strategy_results.csv'
    df.to_csv(output_path, index=False)
    print(f"\n📁 Results saved to: {output_path}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    import sys
    
    start = sys.argv[1] if len(sys.argv) > 1 else '2020-01-01'
    end = sys.argv[2] if len(sys.argv) > 2 else '2025-12-31'
    
    trades, equity = run_backtest(start, end)
