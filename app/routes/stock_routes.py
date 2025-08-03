from flask import Blueprint, jsonify, request, session, send_file
from ..utils.data_store import portfolio_store
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
import io

logger = logging.getLogger(__name__)

stock_bp = Blueprint('stock', __name__, url_prefix='/api')

@stock_bp.before_request
def load_portfolio():
    """Load portfolio data before each request"""
    portfolio_store.load_from_session()

@stock_bp.route('/stock/<symbol>', methods=['GET'])
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

        # Get current price and currency information
        info = stock.info
        current_price = info.get('regularMarketPrice')
        currency = info.get('currency', 'USD')
        
        if not current_price and len(hist) > 0:
            current_price = float(hist['Close'].iloc[-1])
        
        if not current_price:
            return jsonify({'error': f'No price data available for {symbol}'}), 404

        # Convert to INR if necessary
        price_in_inr = current_price
        if currency == 'USD':
            # You might want to fetch real-time forex rates here
            usd_to_inr = 83.0  # Example fixed rate
            price_in_inr = current_price * usd_to_inr
            logger.debug(f"Converting {current_price} USD to {price_in_inr} INR")

        # Calculate returns safely
        day_return = 0
        year_return = 0

        # Calculate 1-day return using historical data
        if len(hist) >= 2:
            try:
                yesterday_close = float(hist['Close'].iloc[-2])
                if currency == 'USD':
                    yesterday_close *= usd_to_inr
                day_return = ((price_in_inr - yesterday_close) / yesterday_close) * 100
                logger.debug(f"Day return calculation: {day_return}%")
            except Exception as e:
                logger.error(f"Error calculating day return: {e}")

        # Get 1-year history for annual return
        try:
            year_hist = stock.history(period='1y')
            if len(year_hist) > 0:
                year_ago_price = float(year_hist['Close'].iloc[0])
                if currency == 'USD':
                    year_ago_price *= usd_to_inr
                year_return = ((price_in_inr - year_ago_price) / year_ago_price) * 100
                logger.debug(f"Year return calculation: {year_return}%")
        except Exception as e:
            logger.error(f"Error calculating year return: {e}")

        # Create response data
        stock_data = {
            'symbol': symbol,
            'price': round(float(price_in_inr), 2),
            'originalPrice': round(float(current_price), 2),
            'originalCurrency': currency,
            'dayReturn': round(float(day_return), 2),
            'yearReturn': round(float(year_return), 2),
            'name': info.get('longName', symbol),
            'currency': 'INR',
            'quantity': int(request.args.get('quantity', 0))
        }

        logger.debug(f"Processed data for {symbol}: {stock_data}")
        
        if stock_data['quantity'] > 0:
            portfolio_store.add_stock(stock_data)
        
        return jsonify(stock_data)
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data for {symbol}'}), 500

@stock_bp.route('/portfolio', methods=['GET'])
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

@stock_bp.route('/portfolio/<symbol>', methods=['DELETE'])
def remove_stock(symbol):
    """Remove stock from portfolio"""
    try:
        portfolio_store.remove_stock(symbol)
        # Return updated portfolio data after deletion
        return jsonify({
            'message': f'Removed {symbol} from portfolio',
            'data': portfolio_store.get_portfolio().to_dict('records'),
            'total_value': portfolio_store.get_total_value(),
            'day_return': portfolio_store.get_returns()[0],
            'year_return': portfolio_store.get_returns()[1]
        })
    except Exception as e:
        logger.error(f"Error removing stock {symbol}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/portfolio/export', methods=['GET'])
def export_portfolio_get():
    """Export portfolio to Excel file"""
    try:
        portfolio_df = portfolio_store.get_portfolio()
        
        if portfolio_df.empty:
            return jsonify({'error': 'No portfolio data to export'}), 404
        
        # Create a BytesIO object to hold the Excel file in memory
        output = io.BytesIO()
        
        # Write to Excel in memory
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            portfolio_df.to_excel(writer, index=False, sheet_name='Portfolio')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Portfolio']
            for idx, col in enumerate(portfolio_df.columns):
                max_length = max(
                    portfolio_df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        # Seek to start of file
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'portfolio_export_{timestamp}.xlsx'
        
        # Return file directly from memory
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting portfolio: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to export portfolio'}), 500

@stock_bp.route('/portfolio/export', methods=['POST'])
def export_portfolio():
    """Export portfolio to Excel file"""
    try:
        portfolio_df = portfolio_store.get_portfolio()
        
        if portfolio_df.empty:
            return jsonify({'error': 'No portfolio data to export'}), 404
            
        # Get save path from request
        save_path = request.json.get('savePath')
        if not save_path:
            return jsonify({'error': 'No save path provided'}), 400
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Write to Excel file
        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            portfolio_df.to_excel(writer, index=False, sheet_name='Portfolio')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Portfolio']
            for idx, col in enumerate(portfolio_df.columns):
                max_length = max(
                    portfolio_df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
        
        return jsonify({
            'message': 'Portfolio exported successfully',
            'filepath': save_path
        })
        
    except Exception as e:
        logger.error(f"Error exporting portfolio: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to export portfolio'}), 500

@stock_bp.route('/portfolio/download', methods=['GET'])
def download_portfolio():
    """Generate portfolio Excel file"""
    try:
        portfolio_df = portfolio_store.get_portfolio()
        
        if portfolio_df.empty:
            return jsonify({'error': 'No portfolio data to export'}), 404

        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            portfolio_df.to_excel(writer, index=False, sheet_name='Portfolio')
            
            # Format the worksheet
            worksheet = writer.sheets['Portfolio']
            for idx, col in enumerate(portfolio_df.columns):
                max_length = max(
                    portfolio_df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error generating portfolio file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to generate portfolio file'}), 500