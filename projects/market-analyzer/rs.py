"""
Relative Strength Backend API
Provides relative strength calculations for stocks
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define stock universes

US_SYMBOLS = [
    '^GSPC', '^NDX', 'AAPL', 'ABBV', 'ABNB', 'ADBE', 'ADI', 'ADSK', 'AMD', 'AMGN',
    'AMZN', 'ANET', 'APA', 'APH', 'APP', 'ARM', 'ASML', 'AVGO', 'BAC', 'BKR',
    'BMNR', 'CB', 'CCL', 'CDNS', 'CEG', 'CME', 'COIN', 'CRM', 'CRWD', 'DDOG',
    'DLTR', 'DXCM', 'EOSE', 'EQIX', 'EXPE', 'FCX', 'FTNT', 'FUTU', 'GDX', 'GEV','GE','GFS'
    'GILD', 'GOOG', 'GS', 'HD', 'HSY', 'IBM', 'ICE', 'IDXX', 'INTC', 'INTU',
    'ISRG', 'J', 'JNJ', 'JPM', 'KLAC', 'KO', 'LLY', 'LMT', 'LOW', 'LRCX',
    'LULU', 'MA', 'MDB', 'META', 'MMM', 'MRK', 'MRVL', 'MS', 'MSFT', 'MSTR',
    'MU', 'NBIS', 'NEE', 'NET', 'NFLX', 'NOW', 'NRG', 'NVDA', 'NVO', 'OKLO',
    'OKTA', 'ON', 'ORCL', 'OXY', 'PANW', 'PDD', 'PEP', 'PFE', 'PGR', 'PLTR',
    'PYPL', 'QBTS', 'QCOM', 'QQQ', 'RKLB', 'SBUX', 'SHOP', 'SMCI', 'SMH', 'SMR',
    'SNOW', 'SNPS', 'TEAM', 'TER', 'TGT', 'TMO', 'TMUS', 'TSLA', 'TSM', 'TTD',
    'TTWO', 'TWLO', 'ULTA', 'UNH', 'UPS', 'V', 'VST', 'VZ', 'WDAY', 'XLB',
    'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'XOM',
    'YUM', 'ZS'
]

HK_SYMBOLS = [

    '^HSI', '0001.HK', '0003.HK', '0005.HK', '0006.HK', '0011.HK', '0012.HK', '0016.HK', '0017.HK', '0019.HK',
    '0020.HK', '0027.HK', '0066.HK', '0175.HK', '0241.HK', '0267.HK', '0268.HK', '0285.HK', '0288.HK', '0291.HK',
    '0293.HK', '0300.hk','0358.HK', '0386.HK', '0388.HK', '0390.HK', '0522.HK', '0669.HK', '0688.HK', '0700.HK', '0762.HK',
    '0763.HK', '0772.HK', '0799.HK', '0823.HK', '0836.HK', '0853.HK', '0857.HK', '0868.HK', '0883.HK', '0909.HK',
    '0914.HK', '0916.HK', '0939.HK', '0941.HK', '0960.HK', '0968.HK', '0981.HK', '0991.HK', '0992.HK', '1024.HK',
    '1038.HK', '1044.HK', '1072.HK', '1093.HK', '1109.HK', '1113.HK', '1133.HK', '1177.HK', '1211.HK', '1299.HK',
    '1316.HK', '1347.HK', '1378.HK', '1398.HK', '1772.HK', '1776.HK', '1787.HK', '1800.HK', '1801.HK', '1810.HK',
    '1818.HK', '1833.HK', '1860.HK', '1876.HK', '1898.HK', '1928.HK', '1929.HK', '1951.HK', '1997.HK', '2007.HK',
    '2013.HK', '2015.HK', '2018.HK', '2208.HK', '2233.HK', '2238.HK', '2252.HK', '2269.HK', '2313.HK', '2318.HK',
    '2319.HK', '2331.HK', '2333.HK', '2382.HK', '2388.HK', '2400.HK', '2498.HK', '2511.HK', '2518.HK', '2522.HK',
    '2533.HK', '2600.HK', '2601.HK', '2628.HK', '2643.HK', '2727.HK', '3690.HK', '3750.HK', '3888.HK', '3968.HK',
    '3988.HK', '6060.HK', '6078.HK', '6098.HK', '6618.HK', '6655.HK', '6681.HK', '6682.HK', '6690.HK', '6699.HK',
    '6862.HK', '6869.HK', '9618.HK', '9626.HK', '9660.HK', '9698.HK', '9863.HK', '9868.HK', '9880.HK', '9888.HK',
    '9923.HK', '9961.HK', '9973.HK', '9988.HK', '9999.HK'
]
# Benchmarks
US_BENCHMARKS = ['^NDX', '^GSPC']
HK_BENCHMARKS = ['^HSI']


def fetch_stock_data(symbols, days=365):
    """Fetch stock data from Yahoo Finance"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching data for {len(symbols)} symbols from {start_date.date()} to {end_date.date()}")
        
        # CORRECTED: Removed group_by='ticker' to match Streamlit logic and create (Price, Ticker) structure
        data = yf.download(symbols, start=start_date, end=end_date, progress=False)

        logger.info(f"Successfully fetched data: {len(data)} rows")

        return data

    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        raise


def calculate_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()


def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_rsi(data, window=14):
    """Calculate RSI indicator"""
    try:
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(com=window-1, min_periods=window).mean()
        avg_loss = loss.ewm(com=window-1, min_periods=window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None

    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return None


def generate_signal(symbol_data):
    """Generate buy/sell signal based on EMA crossover"""
    try:
        if len(symbol_data) < 26:
            return 'neutral'

        # Extract Series safely
        close = symbol_data['Close']
        low = symbol_data['Low']
        high = symbol_data['High']

        ema_short = calculate_ema(close, 5)
        ema_long = calculate_ema(close, 25)
        atr = calculate_atr(high, low, close, 14)

        if pd.isna(atr.iloc[-1]):
            return 'neutral'

        allow_distance = 0.5 * atr.iloc[-1]

        # Buy signal logic
        buy_prep = (low.iloc[-2] < ema_short.iloc[-2]) & \
                   (low.iloc[-2] >= ema_long.iloc[-2] - allow_distance) & \
                   (low.iloc[-2] <= ema_long.iloc[-2] + allow_distance) & \
                   (ema_short.iloc[-2] >= ema_long.iloc[-2])

        buy_signal = buy_prep and (close.iloc[-1] > high.iloc[-2])

        # Sell signal logic
        short_prep = (high.iloc[-2] > ema_short.iloc[-2]) & \
                      (high.iloc[-2] >= ema_long.iloc[-2] - allow_distance) & \
                      (high.iloc[-2] <= ema_long.iloc[-2] + allow_distance) & \
                      (ema_short.iloc[-2] <= ema_long.iloc[-2])

        short_signal = short_prep and (close.iloc[-1] < low.iloc[-2])

        if buy_signal:
            return 'buy'
        elif short_signal:
            return 'sell'
        else:
            return 'neutral'

    except Exception as e:
        logger.error(f"Error generating signal: {str(e)}")
        return 'neutral'


def calculate_relative_strength(close_data, window, date):
    """
    Calculate relative strength scores.
    Accepts ONLY the 'Close' dataframe (matching Streamlit logic)
    """
    try:
        rs_scores = {}
        
        # Ensure we are slicing up to the requested date
        data_slice = close_data.loc[:date]

        for symbol in data_slice.columns:
            try:
                symbol_data = data_slice[symbol]

                # Calculate percentage change over window
                pct_change = symbol_data.pct_change(periods=window)

                if pd.isna(pct_change.iloc[-1]):
                    rs_scores[symbol] = 0
                    continue

                # Compare against all other symbols
                other_data = data_slice.drop(columns=[symbol])
                other_pct_change = other_data.pct_change(periods=window)
                
                # Use numpy for faster comparison
                current_val = pct_change.iloc[-1]
                others_val = other_pct_change.iloc[-1]
                
                outperformance = (current_val > others_val).sum()
                underperformance = (current_val < others_val).sum()

                rs_scores[symbol] = int(outperformance - underperformance)

            except Exception as e:
                logger.error(f"Error calculating RS for {symbol}: {str(e)}")
                rs_scores[symbol] = 0

        return rs_scores

    except Exception as e:
        logger.error(f"Error in calculate_relative_strength: {str(e)}")
        raise


def create_dashboard_data(data, date, rs_scores, benchmarks):
    """Create dashboard data with scores, RSI, and signals"""
    dashboard_stocks = []

    # Sort by RS score
    sorted_scores = sorted(rs_scores.items(), key=lambda x: x[1], reverse=True)

    for symbol, score in sorted_scores:
        try:
            # Handle MultiIndex for full data (Price, Ticker) -> Extract specific Ticker
            if isinstance(data.columns, pd.MultiIndex):
                # Standard yfinance (Price, Ticker) structure
                symbol_data = data.loc[:date, (slice(None), symbol)].droplevel(1, axis=1)
            else:
                # Fallback for single stock or flat structure
                logger.warning(f"Flat structure detected for {symbol}, trying direct access")
                continue # Skip if structure is weird, or handle specifically

            # Calculate RSI
            close_data = symbol_data['Close']
            rsi = calculate_rsi(close_data)

            # Generate signal
            signal = generate_signal(symbol_data) if len(symbol_data) >= 26 else 'neutral'

            dashboard_stocks.append({
                'symbol': symbol,
                'score': score,
                'rsi': rsi,
                'signal': signal,
                'is_benchmark': symbol in benchmarks
            })

        except Exception as e:
            # logger.error(f"Error creating dashboard data for {symbol}: {str(e)}")
            # Fail silently to avoid log spam for missing data, but append with error/0 if needed
            continue

    # Calculate benchmark score
    benchmark_scores = [stock['score'] for stock in dashboard_stocks if stock['is_benchmark']]
    benchmark_score = max(benchmark_scores) if benchmark_scores else 0

    return {
        'stocks': dashboard_stocks,
        'benchmark_score': benchmark_score
    }


def compare_top_stocks(current_data, previous_data, n=10):
    """Compare top N stocks between two periods"""
    current_top = set([s['symbol'] for s in current_data['stocks'][:n]])
    previous_top = set([s['symbol'] for s in previous_data['stocks'][:n]])

    maintained = current_top & previous_top
    new_entries = current_top - previous_top
    dropped_out = previous_top - current_top

    return {
        'maintained': list(maintained),
        'new_entries': list(new_entries),
        'dropped_out': list(dropped_out)
    }


def compare_score_changes(current_data, previous_data, threshold=10):
    """
    Compare score changes between two periods
    Returns stocks with score increases/decreases >= threshold
    """
    # Create dictionaries for quick lookup
    current_scores = {s['symbol']: s['score'] for s in current_data['stocks']}
    previous_scores = {s['symbol']: s['score'] for s in previous_data['stocks']}

    increases = []  # Stocks with +threshold or more
    decreases = []  # Stocks with -threshold or less

    for symbol in current_scores:
        if symbol in previous_scores:
            score_change = current_scores[symbol] - previous_scores[symbol]

            if score_change >= threshold:
                increases.append(symbol)
            elif score_change <= -threshold:
                decreases.append(symbol)

    # Sort by score change magnitude
    increases.sort(key=lambda s: current_scores[s] - previous_scores.get(s, 0), reverse=True)
    decreases.sort(key=lambda s: current_scores[s] - previous_scores.get(s, 0))

    return {
        'increased_by_10': increases,
        'decreased_by_10': decreases
    }


@app.route('/rs', methods=['GET'])
def get_relative_strength():
    """
    Get relative strength analysis
    """
    try:
        market = request.args.get('market', 'US').upper()
        window = int(request.args.get('window', 10))
        compare_days = int(request.args.get('compare_days', 1))

        logger.info(f"RS request: market={market}, window={window}, compare_days={compare_days}")

        # Select symbols and benchmarks based on market
        if market == 'HK':
            symbols = list(set(HK_SYMBOLS))  # Remove duplicates
            benchmarks = HK_BENCHMARKS
        else:  # Default to US
            symbols = list(set(US_SYMBOLS))  # Remove duplicates
            benchmarks = US_BENCHMARKS

        # Fetch data
        data = fetch_stock_data(symbols)

        if data.empty:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404

        # Get current and previous dates
        current_date = data.index[-1]

        # Calculate compare_days back (accounting for trading days)
        date_index = len(data.index) - 1
        previous_date_index = max(0, date_index - compare_days)
        previous_date = data.index[previous_date_index]

        logger.info(f"Current date: {current_date}, Previous date: {previous_date}")

        # Pass only the 'Close' data to the RS calculation (Matching Streamlit Logic)
        close_data = data['Close'] if 'Close' in data.columns else data

        # Calculate RS scores for current and previous dates
        rs_scores_current = calculate_relative_strength(close_data, window, current_date)
        rs_scores_previous = calculate_relative_strength(close_data, window, previous_date)

        # Create dashboard data (Pass full data for RSI/Signal calc)
        current_dashboard = create_dashboard_data(data, current_date, rs_scores_current, benchmarks)
        previous_dashboard = create_dashboard_data(data, previous_date, rs_scores_previous, benchmarks)

        # Create comparisons for multiple periods
        comparison_periods = [2, 5, 10, compare_days]
        comparison_periods = list(set(comparison_periods))  # Remove duplicates
        comparison_periods.sort()

        comparisons = []
        for period in comparison_periods:
            if period >= len(data.index):
                continue

            period_date_index = max(0, date_index - period)
            period_date = data.index[period_date_index]

            rs_scores_period = calculate_relative_strength(close_data, window, period_date)
            period_dashboard = create_dashboard_data(data, period_date, rs_scores_period, benchmarks)

            comparison = compare_top_stocks(current_dashboard, period_dashboard)
            comparison['period'] = period

            # Add score change comparison
            score_changes = compare_score_changes(current_dashboard, period_dashboard, threshold=20)
            comparison['increased_by_10'] = score_changes['increased_by_10']
            comparison['decreased_by_10'] = score_changes['decreased_by_10']

            comparisons.append(comparison)

        result = {
            'success': True,
            'data': {
                'current': current_dashboard,
                'previous': previous_dashboard,
                'current_date': current_date.strftime('%Y-%m-%d'),
                'previous_date': previous_date.strftime('%Y-%m-%d'),
                'comparison': comparisons,
                'metadata': {
                    'market': market,
                    'window': window,
                    'compare_days': compare_days,
                    'num_symbols': len(symbols),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in get_relative_strength: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/rs/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check available symbols"""
    market = request.args.get('market', 'US').upper()

    if market == 'HK':
        symbols = HK_SYMBOLS
        benchmarks = HK_BENCHMARKS
    else:
        symbols = US_SYMBOLS
        benchmarks = US_BENCHMARKS

    return jsonify({
        'market': market,
        'num_symbols': len(symbols),
        'symbols': symbols[:10],  # First 10 symbols
        'benchmarks': benchmarks
    })


if __name__ == '__main__':
    # Run on port 5002 (different from economic data and RRG)
    app.run(host='0.0.0.0', port=5002, debug=True)