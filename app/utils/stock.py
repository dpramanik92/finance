import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_current_price(symbol):
    """Fetch current price for a stock symbol with improved error handling"""
    try:
        print(f"  -> Attempting to fetch price for {symbol}")
        ticker = yf.Ticker(symbol)
        
        # Try recent data first
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            print(f"  -> Got 1-day price: ₹{current_price:.2f}")
            return float(current_price)
        
        # Fallback to 5-day daily data
        print(f"  -> No 1-day data, trying 5-day data...")
        data = ticker.history(period="5d")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            print(f"  -> Got 5-day price: ₹{current_price:.2f}")
            return float(current_price)
        
        # Fallback to basic info
        print(f"  -> No historical data, trying basic info...")
        info = ticker.info
        if 'currentPrice' in info:
            current_price = info['currentPrice']
            print(f"  -> Got current price from info: ₹{current_price:.2f}")
            return float(current_price)
        
        print(f"  -> No price data available for {symbol}")
        return 0.0
        
    except Exception as e:
        print(f"  -> ERROR fetching price for {symbol}: {e}")
        return 0.0

def get_stock_with_benchmark_fallback(symbol, benchmark_symbol='^NSEI'):
    """Get stock data with benchmark fallback for missing historical data"""
    try:
        stock = yf.Ticker(symbol)
        benchmark = yf.Ticker(benchmark_symbol)
        
        # Get 5 years of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        
        stock_data = stock.history(start=start_date, end=end_date)
        benchmark_data = benchmark.history(start=start_date, end=end_date)
        
        if stock_data.empty and not benchmark_data.empty:
            print(f"No data for {symbol}, using benchmark as complete proxy")
            return benchmark_data.copy()
        
        if not stock_data.empty and not benchmark_data.empty:
            # Align and impute missing data
            return _align_and_impute_stock_data(stock_data, benchmark_data, symbol)
        
        return stock_data
        
    except Exception as e:
        print(f"Error in stock data retrieval for {symbol}: {e}")
        return pd.DataFrame()

def _align_and_impute_stock_data(stock_data, benchmark_data, symbol):
    """Helper function to align stock data with benchmark and impute missing values"""
    try:
        # Align stock data to benchmark dates
        aligned_stock = stock_data.reindex(benchmark_data.index)
        
        # Calculate benchmark returns for imputation
        benchmark_returns = benchmark_data['Close'].pct_change().fillna(0)
        
        # Forward fill and then use benchmark returns for remaining gaps
        aligned_stock['Close'] = aligned_stock['Close'].fillna(method='ffill')
        
        # Find still missing values
        missing_mask = aligned_stock['Close'].isna()
        
        if missing_mask.any():
            print(f"Imputing {missing_mask.sum()} data points for {symbol}")
            
            # Use benchmark returns to fill gaps
            last_known_price = None
            for i, (date, is_missing) in enumerate(missing_mask.items()):
                if is_missing:
                    if i > 0 and not pd.isna(aligned_stock['Close'].iloc[i-1]):
                        # Use previous price + benchmark return
                        prev_price = aligned_stock['Close'].iloc[i-1]
                        benchmark_return = benchmark_returns.iloc[i]
                        aligned_stock.loc[date, 'Close'] = prev_price * (1 + benchmark_return)
                    else:
                        # Use benchmark price directly
                        aligned_stock.loc[date, 'Close'] = benchmark_data.loc[date, 'Close']
        
        # Fill other columns based on Close price
        for col in ['Open', 'High', 'Low']:
            if col in aligned_stock.columns:
                aligned_stock[col] = aligned_stock[col].fillna(aligned_stock['Close'])
        
        if 'Volume' in aligned_stock.columns:
            median_volume = aligned_stock['Volume'].median()
            aligned_stock['Volume'] = aligned_stock['Volume'].fillna(median_volume)
        
        return aligned_stock
        
    except Exception as e:
        print(f"Error in data imputation for {symbol}: {e}")
        return stock_data