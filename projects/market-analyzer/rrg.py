"""
JC Algos RRG (Relative Rotation Graph) Backend API
Fetches stock data from Yahoo Finance and calculates RS-Ratio and RS-Momentum

Version: 1.3 - Fixed to include today's real-time delayed price
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define universe configurations
UNIVERSE_CONFIG = {
    "WORLD": {
        "benchmark": "ACWI",
        "description": "全球市場指數",
        "assets": [
            {"ticker": "^GSPC", "label": "標普500"},
            {"ticker": "^NDX", "label": "納指100"},
            {"ticker": "^RUT", "label": "羅素2000"},
            {"ticker": "^HSI", "label": "恆指"},
            {"ticker": "^HSTECH", "label": "恒生科技"},
            {"ticker": "^STOXX50E", "label": "歐洲"},
            {"ticker": "^BSESN", "label": "印度"},
            {"ticker": "^KS11", "label": "韓國"},
            {"ticker": "^TWII", "label": "台灣"},
            {"ticker": "000300.SS", "label": "滬深300"},
            {"ticker": "^N225", "label": "日本"},
            {"ticker": "HYG", "label": "高收益債券"},
            {"ticker": "AGG", "label": "投資級別債券"},
            {"ticker": "EEM", "label": "新興市場"},
            {"ticker": "GDX", "label": "金礦"},
            {"ticker": "XLE", "label": "能源"},
            {"ticker": "XME", "label": "礦業"},
            {"ticker": "AAXJ", "label": "亞太日本除外"},
            {"ticker": "IBB", "label": "生物科技"},
            {"ticker": "DBA", "label": "農業"}
        ]
    },
    "US": {
        "benchmark": "^GSPC",
        "description": "標普500指數",
        "assets": [
            {"ticker": "XLK", "label": "科技"},
            {"ticker": "XLY", "label": "非必須消費"},
            {"ticker": "XLV", "label": "健康護理"},
            {"ticker": "XLF", "label": "金融"},
            {"ticker": "XLC", "label": "通訊"},
            {"ticker": "XLI", "label": "工業"},
            {"ticker": "XLE", "label": "能源"},
            {"ticker": "XLB", "label": "物料"},
            {"ticker": "XLP", "label": "必須消費"},
            {"ticker": "XLU", "label": "公用"},
            {"ticker": "XLRE", "label": "房地產"}
        ]
    },
    "HK": {
        "benchmark": "^HSI",
        "description": "恆生指數",
        "assets": [
            {"ticker": "^HSNU", "label": "公用"},
            {"ticker": "^HSNF", "label": "金融"},
            {"ticker": "^HSNP", "label": "地產"},
            {"ticker": "^HSNC", "label": "工商"}
        ]
    },
    "FX": {
        "benchmark": "HKDUSD=X",
        "description": "港元兌美元",
        "assets": [
            {"ticker": "EURUSD=X", "label": "EUR"},
            {"ticker": "GBPUSD=X", "label": "GBP"},
            {"ticker": "JPYUSD=X", "label": "JPY"},
            {"ticker": "AUDUSD=X", "label": "AUD"},
            {"ticker": "NZDUSD=X", "label": "NZD"},
            {"ticker": "CADUSD=X", "label": "CAD"},
            {"ticker": "CHFUSD=X", "label": "CHF"},
            {"ticker": "CNYUSD=X", "label": "CNY"},
            {"ticker": "EURGBP=X", "label": "EURGBP"},
            {"ticker": "AUDNZD=X", "label": "AUDNZD"},
            {"ticker": "AUDCAD=X", "label": "AUDCAD"},
            {"ticker": "NZDCAD=X", "label": "NZDCAD"},
            {"ticker": "DX-Y.NYB", "label": "DXY"}
        ]
    }
}

# Sector breakdown for US sectors
US_SECTOR_STOCKS = {
    "XLK": {
        "name": "Technology",
        "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "MU", "CRM", "ASML", "SNPS", "IBM", 
                   "INTC", "TXN", "NOW", "QCOM", "AMD", "AMAT", "PANW", "CDNS"]
    },
    "XLY": {
        "name": "Consumer Discretionary",
        "stocks": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "MAR", 
                   "F", "GM", "ORLY", "DHI", "CMG", "YUM", "LEN", "ULTA", "CCL", "EXPE"]
    },
    "XLV": {
        "name": "Health Care",
        "stocks": ["UNH", "JNJ", "LLY", "PFE", "ABT", "TMO", "MRK", "ABBV", "DHR", "BMY", 
                   "AMGN", "CVS", "ISRG", "MDT", "GILD", "VRTX", "CI", "ZTS", "BSX", "HCA"]
    },
    "XLF": {
        "name": "Financials",
        "stocks": ["BRK-B", "JPM", "BAC", "WFC", "GS", "MS", "SPGI", "BLK", "C", "AXP", 
                   "CB", "MMC", "PGR", "PNC", "TFC", "V", "MA", "PYPL", "AON", "CME", "ICE", "COF"]
    },
    "XLC": {
        "name": "Communications",
        "stocks": ["META", "GOOGL", "GOOG", "NFLX", "CMCSA", "DIS", "VZ", "T", "TMUS", 
                   "EA", "TTWO", "MTCH", "CHTR", "FOXA", "FOX", "NWS", "WBD"]
    },
    "XLI": {
        "name": "Industrials",
        "stocks": ["UNP", "HON", "UPS", "BA", "CAT", "GE", "MMM", "RTX", "LMT", "FDX", 
                   "DE", "ETN", "EMR", "NSC", "CSX", "ADP", "GD", "NOC", "JCI", "CARR", "ITW"]
    },
    "XLE": {
        "name": "Energy",
        "stocks": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI", 
                   "WMB", "HES", "HAL", "DVN", "BKR", "CTRA", "EQT", "APA", "MRO", "TRGP", "FANG"]
    },
    "XLB": {
        "name": "Materials",
        "stocks": ["LIN", "APD", "SHW", "FCX", "ECL", "NEM", "DOW", "DD", "CTVA", "PPG", 
                   "NUE", "VMC", "ALB", "FMC", "CE", "MLM", "IFF", "STLD", "CF"]
    },
    "XLP": {
        "name": "Consumer Staples",
        "stocks": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "EL", "CL", "GIS", 
                   "KMB", "SYY", "KHC", "STZ", "HSY", "TGT", "ADM", "MNST", "DG", "DLTR", "WBA", "SJM"]
    },
    "XLU": {
        "name": "Utilities",
        "stocks": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "PCG", "WEC", 
                   "ES", "ED", "DTE", "AEE", "ETR", "CEG", "EIX", "CMS", "CNP", "PPL"]
    },
    "XLRE": {
        "name": "Real Estate",
        "stocks": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "SPG", "SBAC", "AVB", 
                   "EQR", "DLR", "VTR", "ARE", "CBRE", "WY", "EXR", "MAA", "IRM", "ESS", "HST"]
    }
}

# Sector breakdown for HK sub-indexes
HK_SUBINDEX_STOCKS = {
    "^HSNU": {
        "name": "Utilities",
        "stocks": ["0002.HK", "0003.HK", "0006.HK", "0836.HK", "1038.HK", "2688.HK"]
    },
    "^HSNF": {
        "name": "Financials",
        "stocks": ["0005.HK", "0011.HK", "0388.HK", "0939.HK", "1398.HK", "2318.HK", 
                   "2388.HK", "2628.HK", "3968.HK", "3988.HK", "1299.HK"]
    },
    "^HSNP": {
        "name": "Properties",
        "stocks": ["0012.HK", "0016.HK", "0017.HK", "0101.HK", "0823.HK", "0688.HK", 
                   "1109.HK", "1997.HK", "1209.HK", "0960.HK", "1113.HK"]
    },
    "^HSNC": {
        "name": "Commerce & Industry",
        "stocks": ["0700.HK", "0857.HK", "0883.HK", "0941.HK", "0001.HK", "0175.HK", 
                   "0241.HK", "0267.HK", "0285.HK", "0027.HK", "0288.HK", "0291.HK", 
                   "0316.HK", "0332.HK", "0386.HK", "0669.HK", "0762.HK", "0968.HK", "0981.HK"]
    }
}


def get_realtime_price(ticker):
    """
    Get real-time delayed price for a single ticker
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('regularMarketPrice')
        if price is None:
            price = info.get('currentPrice')
        return price
    except Exception as e:
        logger.warning(f"Could not get realtime price for {ticker}: {e}")
        return None


def calculate_ma(data, period):
    """Calculate moving average"""
    return data.rolling(window=period).mean()


def calculate_rrg_values(asset_data, benchmark_data):
    """
    Calculate RS-Ratio and RS-Momentum for RRG
    """
    sbr = asset_data / benchmark_data
    rs1 = calculate_ma(sbr, 10)
    rs2 = calculate_ma(sbr, 26)
    rs_ratio = 100 * ((rs1 - rs2) / rs2 + 1)
    rm1 = calculate_ma(rs_ratio, 1)
    rm2 = calculate_ma(rs_ratio, 4)
    rs_momentum = 100 * ((rm1 - rm2) / rm2 + 1)
    return rs_ratio, rs_momentum


def fetch_stock_data(tickers, timeframe='weekly', weeks=100):
    """
    Fetch stock data from Yahoo Finance with real-time prices appended
    """
    try:
        end_date = datetime.now()
        if timeframe == 'weekly':
            start_date = end_date - timedelta(weeks=weeks)
        else:
            start_date = end_date - timedelta(days=weeks * 7)

        logger.info(f"Fetching data for {len(tickers)} tickers from {start_date.date()} to {end_date.date()}")

        # Download historical data
        data = yf.download(
            tickers,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True
        )['Close']

        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])

        # Resample to weekly if needed
        if timeframe == 'weekly':
            data = data.resample('W-FRI').last()

        # Forward fill missing values
        data = data.ffill(limit=5)

        # Append today's real-time prices if not already included
        today = pd.Timestamp(datetime.now().date())
        last_data_date = data.index[-1].date() if len(data) > 0 else None
        
        if last_data_date and last_data_date < datetime.now().date():
            logger.info(f"Last data date is {last_data_date}, fetching real-time prices for today")
            
            realtime_prices = {}
            for ticker in tickers:
                price = get_realtime_price(ticker)
                if price is not None:
                    realtime_prices[ticker] = price
            
            if realtime_prices:
                # Create a new row with today's date
                if timeframe == 'weekly':
                    # For weekly, use next Friday or today
                    today_ts = pd.Timestamp(datetime.now())
                    days_until_friday = (4 - today_ts.weekday()) % 7
                    if days_until_friday == 0 and datetime.now().hour < 16:
                        next_friday = today_ts
                    else:
                        next_friday = today_ts + timedelta(days=days_until_friday)
                    new_index = pd.Timestamp(next_friday.date())
                else:
                    new_index = pd.Timestamp(datetime.now().date())
                
                # Only add if this date doesn't exist
                if new_index not in data.index:
                    new_row = pd.Series(index=data.columns, dtype=float)
                    for ticker in data.columns:
                        if ticker in realtime_prices:
                            new_row[ticker] = realtime_prices[ticker]
                        else:
                            new_row[ticker] = data[ticker].iloc[-1]  # Use last known price
                    
                    data.loc[new_index] = new_row
                    data = data.sort_index()
                    logger.info(f"Added real-time prices for {new_index.date()}")

        logger.info(f"Successfully fetched data: {data.shape[0]} rows, {data.shape[1]} columns")
        return data

    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        raise


@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "RRG Backend API",
        "version": "1.3",
        "endpoints": {
            "/rrg": "GET - Fetch RRG data (params: universe, timeframe, tail_length, sector)",
            "/rrg/custom": "GET - Fetch RRG data for custom ticker list (params: market, tickers, timeframe, tail_length)"
        }
    })


@app.route('/rrg', methods=['GET'])
def get_rrg_data():
    """
    Fetch RRG data for specified universe
    """
    try:
        universe = request.args.get('universe', 'WORLD').upper()
        timeframe = request.args.get('timeframe', 'weekly').lower()
        tail_length = int(request.args.get('tail_length', 3))
        sector = request.args.get('sector', None)

        logger.info(f"RRG request: universe={universe}, timeframe={timeframe}, tail_length={tail_length}, sector={sector}")

        if universe == 'US_SECTORS':
            if not sector or sector not in US_SECTOR_STOCKS:
                return jsonify({
                    "success": False,
                    "error": f"Invalid or missing sector. Must be one of: {', '.join(US_SECTOR_STOCKS.keys())}"
                }), 400
            
            sector_info = US_SECTOR_STOCKS[sector]
            benchmark_ticker = sector
            description = f"{sector_info['name']} Sector - {sector}"
            assets = [{"ticker": stock, "label": stock} for stock in sector_info['stocks']]
        
        elif universe == 'HK_SUBINDEXES':
            if not sector or sector not in HK_SUBINDEX_STOCKS:
                return jsonify({
                    "success": False,
                    "error": f"Invalid or missing sector. Must be one of: {', '.join(HK_SUBINDEX_STOCKS.keys())}"
                }), 400
            
            sector_info = HK_SUBINDEX_STOCKS[sector]
            benchmark_ticker = sector
            description = f"{sector_info['name']} - {sector}"
            assets = [{"ticker": stock, "label": stock.replace('.HK', '')} for stock in sector_info['stocks']]
        
        else:
            if universe not in UNIVERSE_CONFIG:
                return jsonify({
                    "success": False,
                    "error": f"Invalid universe. Must be one of: {', '.join(UNIVERSE_CONFIG.keys())}, US_SECTORS, HK_SUBINDEXES"
                }), 400

            config = UNIVERSE_CONFIG[universe]
            benchmark_ticker = config["benchmark"]
            description = config["description"]
            assets = config["assets"]

        all_tickers = [benchmark_ticker] + [asset["ticker"] for asset in assets]
        data = fetch_stock_data(all_tickers, timeframe=timeframe)

        if benchmark_ticker not in data.columns:
            return jsonify({
                "success": False,
                "error": f"No data available for benchmark {benchmark_ticker}"
            }), 500

        results = []
        benchmark_data = data[benchmark_ticker]

        for asset in assets:
            ticker = asset["ticker"]
            label = asset["label"]

            if ticker not in data.columns:
                logger.warning(f"No data for ticker {ticker}, skipping")
                continue

            asset_data = data[ticker]
            rs_ratio, rs_momentum = calculate_rrg_values(asset_data, benchmark_data)

            valid_data = rs_ratio.dropna()
            if len(valid_data) < tail_length + 1:
                logger.warning(f"Not enough data for {ticker}, skipping")
                continue

            trail_data = []
            for i in range(-tail_length, 0):
                if pd.notna(rs_ratio.iloc[i]) and pd.notna(rs_momentum.iloc[i]):
                    trail_data.append([
                        round(float(rs_ratio.iloc[i]), 2),
                        round(float(rs_momentum.iloc[i]), 2)
                    ])

            current_rs_ratio = round(float(rs_ratio.iloc[-1]), 2)
            current_rs_momentum = round(float(rs_momentum.iloc[-1]), 2)

            results.append({
                "name": ticker,
                "label": label,
                "rsRatio": current_rs_ratio,
                "rsMomentum": current_rs_momentum,
                "trail": trail_data
            })

        return jsonify({
            "success": True,
            "data": {
                "benchmark": benchmark_ticker,
                "description": description,
                "assets": results,
                "metadata": {
                    "universe": universe,
                    "sector": sector,
                    "timeframe": timeframe,
                    "tail_length": tail_length,
                    "data_points": len(data),
                    "last_updated": data.index[-1].strftime("%Y-%m-%d") if len(data) > 0 else None
                }
            }
        })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"success": False, "error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error processing RRG request: {str(e)}")
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@app.route('/rrg/custom', methods=['GET'])
def get_rrg_custom():
    """
    Fetch RRG data for custom ticker list (user portfolio)
    """
    try:
        market = request.args.get('market', 'US').upper()
        tickers_param = request.args.get('tickers', '')
        timeframe = request.args.get('timeframe', 'weekly').lower()
        tail_length = int(request.args.get('tail_length', 3))
        
        logger.info(f"Custom RRG request: market={market}, tickers={tickers_param}, timeframe={timeframe}")
        
        if market not in ['HK', 'US']:
            return jsonify({"success": False, "error": "Invalid market. Must be 'HK' or 'US'"}), 400
        
        if not tickers_param:
            return jsonify({"success": False, "error": "No tickers provided"}), 400
        
        ticker_list = [t.strip() for t in tickers_param.split(',') if t.strip()]
        
        if len(ticker_list) == 0:
            return jsonify({"success": False, "error": "No valid tickers provided"}), 400
        
        if market == 'HK':
            benchmark_ticker = '^HSI'
            description = '我的港股組合 (My HK Portfolio)'
        else:
            benchmark_ticker = '^GSPC'
            description = '我的美股組合 (My US Portfolio)'
        
        assets = []
        for ticker in ticker_list:
            if market == 'HK' and ticker.upper().endswith('.HK'):
                label = ticker[:-3]
            else:
                label = ticker
            assets.append({"ticker": ticker, "label": label})
        
        all_tickers = [benchmark_ticker] + [asset["ticker"] for asset in assets]
        data = fetch_stock_data(all_tickers, timeframe=timeframe)
        
        if benchmark_ticker not in data.columns:
            return jsonify({"success": False, "error": f"No data available for benchmark {benchmark_ticker}"}), 500
        
        results = []
        benchmark_data = data[benchmark_ticker]
        
        for asset in assets:
            ticker = asset["ticker"]
            label = asset["label"]
            
            if ticker not in data.columns:
                logger.warning(f"No data for ticker {ticker}, skipping")
                continue
            
            asset_data = data[ticker]
            rs_ratio, rs_momentum = calculate_rrg_values(asset_data, benchmark_data)
            
            valid_data = rs_ratio.dropna()
            if len(valid_data) < tail_length + 1:
                logger.warning(f"Not enough data for {ticker}, skipping")
                continue
            
            trail_data = []
            for i in range(-tail_length, 0):
                if pd.notna(rs_ratio.iloc[i]) and pd.notna(rs_momentum.iloc[i]):
                    trail_data.append([
                        round(float(rs_ratio.iloc[i]), 2),
                        round(float(rs_momentum.iloc[i]), 2)
                    ])
            
            current_rs_ratio = round(float(rs_ratio.iloc[-1]), 2)
            current_rs_momentum = round(float(rs_momentum.iloc[-1]), 2)
            
            results.append({
                "name": ticker,
                "label": label,
                "rsRatio": current_rs_ratio,
                "rsMomentum": current_rs_momentum,
                "trail": trail_data
            })
        
        return jsonify({
            "success": True,
            "data": {
                "benchmark": benchmark_ticker,
                "description": description,
                "assets": results,
                "metadata": {
                    "universe": f"MY_{market}_PORTFOLIO",
                    "market": market,
                    "timeframe": timeframe,
                    "tail_length": tail_length,
                    "data_points": len(data),
                    "last_updated": data.index[-1].strftime("%Y-%m-%d") if len(data) > 0 else None
                }
            }
        })
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"success": False, "error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error processing custom RRG request: {str(e)}")
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@app.route('/sectors', methods=['GET'])
def get_sectors():
    """Get available sectors for US and HK"""
    return jsonify({
        "success": True,
        "data": {
            "US_SECTORS": {k: v["name"] for k, v in US_SECTOR_STOCKS.items()},
            "HK_SUBINDEXES": {k: v["name"] for k, v in HK_SUBINDEX_STOCKS.items()}
        }
    })


@app.route('/debug', methods=['GET'])
def debug():
    """Debug endpoint to test data fetching"""
    try:
        universe = request.args.get('universe', 'US')
        config = UNIVERSE_CONFIG.get(universe.upper(), UNIVERSE_CONFIG['US'])
        test_tickers = [config["benchmark"], config["assets"][0]["ticker"]]

        logger.info(f"Debug: Fetching test data for {test_tickers}")
        data = fetch_stock_data(test_tickers, timeframe='weekly', weeks=20)

        return jsonify({
            "success": True,
            "tickers": test_tickers,
            "data_shape": data.shape,
            "columns": list(data.columns),
            "last_5_rows": data.tail().to_dict(),
            "date_range": {
                "start": data.index.min().strftime("%Y-%m-%d"),
                "end": data.index.max().strftime("%Y-%m-%d")
            }
        })
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)