#!/usr/bin/env python3
"""
BB Squeeze Backtest - Option 3: ETF Proxy + High Volume Stocks
Metrics: Win Rate, Profit Factor, Sharpe, Sortino, Calmar, Max Drawdown
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load all 132 HSI constituents
import json
def load_hsi_constituents():
    try:
        with open('/root/clawd/hsi_constituents.json', 'r') as f:
            return json.load(f)
    except:
        return {}

TEST_UNIVERSE = load_hsi_constituents()

# Strategy Parameters
BB_PERIOD = 20
BB_STD = 2
RSI_PERIOD = 14
SQUEEZE_THRESHOLD = 0.03  # 3% (best performing)

# Backtest Parameters
INITIAL_CAPITAL = 1_000_000  # HKD
POSITION_SIZE = 0.05  # 5% per trade
COMMISSION = 0.001  # 0.1%
STAMP_DUTY = 0.001  # 0.1%
SLIPPAGE = 0.001  # 0.1%

# Risk Management
STOP_LOSS_ATR_MULT = 2.0  # SL at breakout high/low +/- 2 ATR
TAKE_PROFIT_1_R_MULT = 1.5  # First TP: 50% position
TAKE_PROFIT_2_R_MULT = 2.5  # Second TP: remaining 50%
MAX_HOLDING_DAYS = 10  # 10 days time stop

# =============================================================================
# INDICATOR CALCULATIONS
# =============================================================================

def calculate_indicators(df):
    """Calculate BB, RSI, ATR, EMA200"""
    # Bollinger Bands
    df['SMA'] = df['Close'].rolling(BB_PERIOD).mean()
    df['STD'] = df['Close'].rolling(BB_PERIOD).std()
    df['BB_Upper'] = df['SMA'] + (BB_STD * df['STD'])
    df['BB_Lower'] = df['SMA'] - (BB_STD * df['STD'])
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA']
    df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # EMA 200 for trend filter
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['Above_EMA200'] = df['Close'] > df['EMA200']
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(RSI_PERIOD).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR for stop loss
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.maximum(
            abs(df['High'] - df['Close'].shift(1)),
            abs(df['Low'] - df['Close'].shift(1))
        )
    )
    df['ATR'] = df['TR'].rolling(14).mean()
    
    # Volume MA
    df['Vol_MA'] = df['Volume'].rolling(20).mean()
    
    return df

def detect_squeeze(row):
    """Detect BB squeeze condition"""
    return row['BB_Width'] < SQUEEZE_THRESHOLD

def get_signal(df, i, min_bars=200):
    """
    FADE THE BREAKOUT strategy
    Short breakouts above upper band, Long breakouts below lower band
    Returns: 1 (Long), -1 (Short), 0 (No signal)
    """
    if i < 30:
        return 0
    
    curr = df.iloc[i]
    prev = df.iloc[i-1]
    
    # Check if previous bar was in squeeze
    if not detect_squeeze(prev):
        return 0
    
    # FADE UPWARD BREAKOUT: Price breaks above upper band -> SHORT
    # Expect failed breakout and reversion down
    if curr['Close'] > prev['BB_Upper']:
        return -1
    
    # FADE DOWNWARD BREAKOUT: Price breaks below lower band -> LONG
    # Expect failed breakout and reversion up
    if curr['Close'] < prev['BB_Lower']:
        return 1
    
    return 0

# =============================================================================
# BACKTEST ENGINE
# =============================================================================

class Trade:
    def __init__(self, symbol, entry_date, entry_price, direction, size, stop_loss, take_profit_1, take_profit_2):
        self.symbol = symbol
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.direction = direction  # 1 or -1
        self.size = size
        self.remaining_size = size
        self.stop_loss = stop_loss
        self.take_profit_1 = take_profit_1  # 1.5R
        self.take_profit_2 = take_profit_2  # 2R
        self.tp1_hit = False
        self.exit_date = None
        self.exit_price = None
        self.pnl = 0
        self.pnl_pct = 0
        self.holding_days = 0
        self.exit_reason = None

def backtest_symbol(symbol, name, start_date='2021-01-01', end_date='2025-12-31'):
    """Backtest single symbol with partial TP (1.5R + 2R)"""
    
    # Download data
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        if len(df) < 100:
            print(f"  ⚠️ {symbol}: Insufficient data ({len(df)} rows)")
            return []
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
        return []
    
    df = calculate_indicators(df)
    df = df.dropna()
    
    trades = []
    position = None
    partial_pnl = 0  # Track partial profit from TP1
    
    for i in range(BB_PERIOD + 5, len(df)):
        curr = df.iloc[i]
        date = df.index[i]
        
        # Check exit conditions if in position
        if position:
            position.holding_days += 1
            
            # Check TP1 first (1.5R) - take 50% off
            if not position.tp1_hit:
                if position.direction == 1 and curr['High'] >= position.take_profit_1:
                    # Partial exit at TP1
                    partial_size = position.size // 2
                    partial_pnl = (position.take_profit_1 - position.entry_price) * position.direction * partial_size
                    partial_pnl -= position.entry_price * partial_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
                    position.remaining_size = position.size - partial_size
                    position.tp1_hit = True
                    # Move stop to breakeven
                    position.stop_loss = position.entry_price
                elif position.direction == -1 and curr['Low'] <= position.take_profit_1:
                    partial_size = position.size // 2
                    partial_pnl = (position.entry_price - position.take_profit_1) * partial_size
                    partial_pnl -= position.entry_price * partial_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
                    position.remaining_size = position.size - partial_size
                    position.tp1_hit = True
                    position.stop_loss = position.entry_price
            
            # Stop Loss
            if position.direction == 1 and curr['Low'] <= position.stop_loss:
                position.exit_price = position.stop_loss
                position.exit_date = date
                position.exit_reason = 'Stop Loss' if not position.tp1_hit else 'TP1+BE Stop'
            elif position.direction == -1 and curr['High'] >= position.stop_loss:
                position.exit_price = position.stop_loss
                position.exit_date = date
                position.exit_reason = 'Stop Loss' if not position.tp1_hit else 'TP1+BE Stop'
            
            # Take Profit 2 (2R) - exit remaining
            elif position.direction == 1 and curr['High'] >= position.take_profit_2:
                position.exit_price = position.take_profit_2
                position.exit_date = date
                position.exit_reason = 'Take Profit 2R'
            elif position.direction == -1 and curr['Low'] <= position.take_profit_2:
                position.exit_price = position.take_profit_2
                position.exit_date = date
                position.exit_reason = 'Take Profit 2R'
            
            # Time-based exit
            elif position.holding_days >= MAX_HOLDING_DAYS:
                position.exit_price = curr['Close']
                position.exit_date = date
                position.exit_reason = 'Time Exit'
            
            # Calculate PnL if exited
            if position.exit_price:
                # PnL from remaining position
                remaining_pnl = (position.exit_price - position.entry_price) * position.direction * position.remaining_size
                remaining_pnl -= position.entry_price * position.remaining_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
                
                position.pnl = partial_pnl + remaining_pnl
                position.pnl_pct = position.pnl / (position.entry_price * position.size) * 100
                trades.append(position)
                position = None
                partial_pnl = 0
        
        # Check entry signal if no position
        if position is None:
            signal = get_signal(df, i, min_bars=50)
            
            if signal == 1:  # Long only
                entry_price = curr['Close']
                atr = curr['ATR']
                risk = STOP_LOSS_ATR_MULT * atr
                
                if signal == 1:  # Long
                    stop_loss = entry_price - risk
                    take_profit_1 = entry_price + (TAKE_PROFIT_1_R_MULT * risk)
                    take_profit_2 = entry_price + (TAKE_PROFIT_2_R_MULT * risk)
                else:  # Short
                    stop_loss = entry_price + risk
                    take_profit_1 = entry_price - (TAKE_PROFIT_1_R_MULT * risk)
                    take_profit_2 = entry_price - (TAKE_PROFIT_2_R_MULT * risk)
                
                size = int((INITIAL_CAPITAL * POSITION_SIZE) / entry_price)
                
                position = Trade(
                    symbol=symbol,
                    entry_date=date,
                    entry_price=entry_price,
                    direction=signal,
                    size=size,
                    stop_loss=stop_loss,
                    take_profit_1=take_profit_1,
                    take_profit_2=take_profit_2
                )
    
    # Close any open position at end
    if position:
        position.exit_price = df.iloc[-1]['Close']
        position.exit_date = df.index[-1]
        position.exit_reason = 'End of Data'
        remaining_pnl = (position.exit_price - position.entry_price) * position.direction * position.remaining_size
        remaining_pnl -= position.entry_price * position.remaining_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
        position.pnl = partial_pnl + remaining_pnl
        position.pnl_pct = position.pnl / (position.entry_price * position.size) * 100
        trades.append(position)
    
    return trades

# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

def calculate_metrics(trades, initial_capital=INITIAL_CAPITAL):
    """Calculate all performance metrics including Calmar Ratio"""
    
    if not trades:
        return None
    
    # Basic stats
    pnls = [t.pnl for t in trades]
    pnl_pcts = [t.pnl_pct for t in trades]
    
    winners = [p for p in pnls if p > 0]
    losers = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    winning_trades = len(winners)
    losing_trades = len(losers)
    
    # Win Rate
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    # Average Win/Loss
    avg_win = np.mean(winners) if winners else 0
    avg_loss = abs(np.mean(losers)) if losers else 0
    
    # Profit Factor
    gross_profit = sum(winners) if winners else 0
    gross_loss = abs(sum(losers)) if losers else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Total Return
    total_pnl = sum(pnls)
    total_return_pct = total_pnl / initial_capital * 100
    
    # Build equity curve
    equity = [initial_capital]
    for pnl in pnls:
        equity.append(equity[-1] + pnl)
    equity = np.array(equity)
    
    # Daily returns (approximate)
    returns = np.diff(equity) / equity[:-1]
    
    # Sharpe Ratio (annualized, assuming 252 trading days)
    risk_free_rate = 0.03  # 3% annual
    excess_returns = returns - (risk_free_rate / 252)
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(returns) if np.std(returns) > 0 else 0
    
    # Sortino Ratio (downside deviation only)
    downside_returns = returns[returns < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0.0001
    sortino = np.sqrt(252) * np.mean(excess_returns) / downside_std if downside_std > 0 else 0
    
    # Max Drawdown
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / peak
    max_drawdown = np.max(drawdown) * 100
    
    # Calmar Ratio (Annual Return / Max Drawdown)
    # Estimate annual return from total return
    years = total_trades / 50  # Rough estimate: ~50 trades per year
    annual_return = (total_return_pct / years) if years > 0 else total_return_pct
    calmar = annual_return / max_drawdown if max_drawdown > 0 else 0
    
    # Expectancy
    expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
    
    # Average holding period
    avg_holding = np.mean([t.holding_days for t in trades])
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'total_pnl': total_pnl,
        'total_return_pct': total_return_pct,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar,
        'expectancy': expectancy,
        'avg_holding_days': avg_holding,
    }

def print_report(metrics, trades):
    """Print formatted backtest report"""
    
    print("\n" + "=" * 70)
    print("📊 BB SQUEEZE BACKTEST REPORT")
    print("=" * 70)
    
    print(f"\n📈 TRADE STATISTICS")
    print("-" * 40)
    print(f"Total Trades:     {metrics['total_trades']}")
    print(f"Winning Trades:   {metrics['winning_trades']}")
    print(f"Losing Trades:    {metrics['losing_trades']}")
    print(f"Win Rate:         {metrics['win_rate']:.1f}%")
    print(f"Avg Holding Days: {metrics['avg_holding_days']:.1f}")
    
    print(f"\n💰 PROFIT/LOSS")
    print("-" * 40)
    print(f"Total PnL:        HK${metrics['total_pnl']:,.0f}")
    print(f"Total Return:     {metrics['total_return_pct']:.2f}%")
    print(f"Avg Win:          HK${metrics['avg_win']:,.0f}")
    print(f"Avg Loss:         HK${metrics['avg_loss']:,.0f}")
    print(f"Profit Factor:    {metrics['profit_factor']:.2f}")
    print(f"Expectancy:       HK${metrics['expectancy']:,.0f}")
    
    print(f"\n📉 RISK METRICS")
    print("-" * 40)
    print(f"Max Drawdown:     {metrics['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio:    {metrics['sortino_ratio']:.2f}")
    print(f"Calmar Ratio:     {metrics['calmar_ratio']:.2f}")
    
    print("\n" + "=" * 70)
    
    # Exit reason breakdown
    exit_reasons = {}
    for t in trades:
        reason = t.exit_reason
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    print(f"\n🚪 EXIT REASONS")
    print("-" * 40)
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        print(f"{reason:20} {count:4} ({count/len(trades)*100:.1f}%)")

# =============================================================================
# MAIN
# =============================================================================

def calculate_indicators_hourly(df):
    """Calculate BB, RSI, ATR with EMA50 for hourly"""
    # Bollinger Bands
    df['SMA'] = df['Close'].rolling(BB_PERIOD).mean()
    df['STD'] = df['Close'].rolling(BB_PERIOD).std()
    df['BB_Upper'] = df['SMA'] + (BB_STD * df['STD'])
    df['BB_Lower'] = df['SMA'] - (BB_STD * df['STD'])
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA']
    df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # EMA50 for hourly trend filter (50 hours ≈ 7 trading days)
    df['EMA200'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['Above_EMA200'] = df['Close'] > df['EMA200']
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(RSI_PERIOD).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.maximum(
            abs(df['High'] - df['Close'].shift(1)),
            abs(df['Low'] - df['Close'].shift(1))
        )
    )
    df['ATR'] = df['TR'].rolling(14).mean()
    
    # Volume MA
    df['Vol_MA'] = df['Volume'].rolling(20).mean()
    
    return df

def backtest_symbol_hourly(symbol, name, start_date='2024-01-01', end_date='2025-12-31'):
    """Backtest single symbol on 1H timeframe with EMA50"""
    
    # Download hourly data (yfinance limits to ~2 years)
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1h')
        if len(df) < 100:
            return []
    except Exception as e:
        return []
    
    df = calculate_indicators_hourly(df)
    df = df.dropna()
    
    trades = []
    position = None
    partial_pnl = 0
    
    # Adjust max holding for hourly (in hours, ~5 trading days = 35 hours)
    max_holding_hours = 35
    
    for i in range(50 + 5, len(df)):
        curr = df.iloc[i]
        date = df.index[i]
        
        if position:
            position.holding_days += 1
            
            # Check TP1 first (1.5R)
            if not position.tp1_hit:
                if position.direction == 1 and curr['High'] >= position.take_profit_1:
                    partial_size = position.size // 2
                    partial_pnl = (position.take_profit_1 - position.entry_price) * position.direction * partial_size
                    partial_pnl -= position.entry_price * partial_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
                    position.remaining_size = position.size - partial_size
                    position.tp1_hit = True
                    position.stop_loss = position.entry_price
            
            # Stop Loss
            if position.direction == 1 and curr['Low'] <= position.stop_loss:
                position.exit_price = position.stop_loss
                position.exit_date = date
                position.exit_reason = 'Stop Loss' if not position.tp1_hit else 'TP1+BE Stop'
            
            # Take Profit 2
            elif position.direction == 1 and curr['High'] >= position.take_profit_2:
                position.exit_price = position.take_profit_2
                position.exit_date = date
                position.exit_reason = 'Take Profit 2R'
            
            # Time exit
            elif position.holding_days >= max_holding_hours:
                position.exit_price = curr['Close']
                position.exit_date = date
                position.exit_reason = 'Time Exit'
            
            if position.exit_price:
                remaining_pnl = (position.exit_price - position.entry_price) * position.direction * position.remaining_size
                remaining_pnl -= position.entry_price * position.remaining_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
                position.pnl = partial_pnl + remaining_pnl
                position.pnl_pct = position.pnl / (position.entry_price * position.size) * 100
                trades.append(position)
                position = None
                partial_pnl = 0
        
        if position is None:
            signal = get_signal(df, i, min_bars=30)
            
            if signal != 0:
                entry_price = curr['Close']
                atr = curr['ATR']
                
                # FADE BREAKOUT: SL at breakout day high/low +/- 2 ATR
                if signal == 1:  # Long (fading downward breakout)
                    # Stop below the low of breakout day
                    stop_loss = curr['Low'] - (STOP_LOSS_ATR_MULT * atr)
                    risk = entry_price - stop_loss
                    take_profit_1 = entry_price + (TAKE_PROFIT_1_R_MULT * risk)
                    take_profit_2 = entry_price + (TAKE_PROFIT_2_R_MULT * risk)
                else:  # Short (fading upward breakout)
                    # Stop above the high of breakout day
                    stop_loss = curr['High'] + (STOP_LOSS_ATR_MULT * atr)
                    risk = stop_loss - entry_price
                    take_profit_1 = entry_price - (TAKE_PROFIT_1_R_MULT * risk)
                    take_profit_2 = entry_price - (TAKE_PROFIT_2_R_MULT * risk)
                
                size = int((INITIAL_CAPITAL * POSITION_SIZE) / entry_price)
                
                position = Trade(
                    symbol=symbol,
                    entry_date=date,
                    entry_price=entry_price,
                    direction=signal,
                    size=size,
                    stop_loss=stop_loss,
                    take_profit_1=take_profit_1,
                    take_profit_2=take_profit_2
                )
    
    if position:
        position.exit_price = df.iloc[-1]['Close']
        position.exit_date = df.index[-1]
        position.exit_reason = 'End of Data'
        remaining_pnl = (position.exit_price - position.entry_price) * position.direction * position.remaining_size
        remaining_pnl -= position.entry_price * position.remaining_size * (COMMISSION + STAMP_DUTY + SLIPPAGE) * 2
        position.pnl = partial_pnl + remaining_pnl
        position.pnl_pct = position.pnl / (position.entry_price * position.size) * 100
        trades.append(position)
    
    return trades

def main():
    print("=" * 70)
    print("🔍 BB SQUEEZE BACKTEST - HK STOCKS (DAILY ONLY)")
    print("=" * 70)
    print(f"Universe: {len(TEST_UNIVERSE)} stocks (All HSI Constituents)")
    print(f"BB Squeeze Threshold: {SQUEEZE_THRESHOLD*100}%")
    print(f"Initial Capital: HK${INITIAL_CAPITAL:,}")
    print("=" * 70)
    
    all_trades = []
    
    # Daily backtest only (2021-2025)
    print("\n" + "=" * 70)
    print("📅 DAILY TIMEFRAME (2021-2025)")
    print("=" * 70)
    
    for symbol, name in TEST_UNIVERSE.items():
        print(f"📊 {symbol} ({name})...", end=" ")
        trades = backtest_symbol(symbol, name)
        print(f"{len(trades)} trades")
        all_trades.extend(trades)
    
    print(f"\n✅ TOTAL trades: {len(all_trades)}")
    
    if all_trades:
        metrics = calculate_metrics(all_trades)
        print_report(metrics, all_trades)
        
        results_df = pd.DataFrame([{
            'symbol': t.symbol,
            'entry_date': t.entry_date,
            'exit_date': t.exit_date,
            'direction': 'Long' if t.direction == 1 else 'Short',
            'entry_price': t.entry_price,
            'exit_price': t.exit_price,
            'pnl': t.pnl,
            'pnl_pct': t.pnl_pct,
            'holding_days': t.holding_days,
            'exit_reason': t.exit_reason
        } for t in all_trades])
        
        results_df.to_csv('/root/clawd/bb_squeeze_backtest_results.csv', index=False)
        print(f"\n📁 Results saved to: /root/clawd/bb_squeeze_backtest_results.csv")
    
    return all_trades, metrics if all_trades else None

if __name__ == "__main__":
    trades, metrics = main()
