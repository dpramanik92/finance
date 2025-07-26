from flask import Blueprint, jsonify, request
from ..utils.data_store import portfolio_store
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    try:
        # Create Ticker object and fetch data with error handling
        stock = yf.Ticker(symbol.upper())
        
        try:
            hist = stock.history(period='2d')
            if hist.empty:
                raise ValueError("No historical data available")
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return jsonify({'error': f'Failed to fetch data for {symbol}'}), 404

        # Get current price from history if regular market price is not available
        info = stock.info
        current_price = info.get('regularMarketPrice')
        if not current_price and len(hist) > 0:
            current_price = float(hist['Close'].iloc[-1])
        
        if not current_price:
            return jsonify({'error': f'No price data available for {symbol}'}), 404

        # Calculate returns safely
        day_return = 0
        year_return = 0

        # Calculate 1-day return using historical data
        if len(hist) >= 2:
            try:
                yesterday_close = float(hist['Close'].iloc[-2])
                day_return = ((current_price - yesterday_close) / yesterday_close) * 100
            except Exception as e:
                logger.error(f"Error calculating day return: {e}")

        # Get 1-year history for annual return
        try:
            year_hist = stock.history(period='1y')
            if len(year_hist) > 0:
                year_ago_price = float(year_hist['Close'].iloc[0])
                year_return = ((current_price - year_ago_price) / year_ago_price) * 100
        except Exception as e:
            logger.error(f"Error calculating year return: {e}")

        # Create response data
        stock_data = {
            'symbol': symbol,
            'price': float(current_price),
            'dayReturn': round(float(day_return), 2),
            'yearReturn': round(float(year_return), 2),
            'name': info.get('longName', symbol),
            'currency': 'INR',
            'quantity': int(request.args.get('quantity', 0))
        }

        logger.debug(f"Processed data for {symbol}: {stock_data}")
        
        return jsonify(stock_data)
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data for {symbol}'}), 500

@stock_bp.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio data"""
    try:
        portfolio = portfolio_store.get_portfolio()
        return jsonify({
            'data': portfolio.to_dict('records'),
            'total_value': portfolio_store.get_total_value(),
            'day_return': portfolio_store.get_returns()[0],
            'year_return': portfolio_store.get_returns()[1]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/api/portfolio/<symbol>', methods=['DELETE'])
def remove_stock(symbol):
    """Remove stock from portfolio"""
    try:
        portfolio_store.remove_stock(symbol)
        return jsonify({'message': f'Removed {symbol} from portfolio'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500