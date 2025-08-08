import yfinance as yf

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