import pandas as pd
from datetime import datetime
from flask import session

class PortfolioDataStore:
    def __init__(self):
        # Define columns explicitly
        self.columns = [
            'symbol', 'quantity', 'price', 'value', 
            'day_return', 'year_return', 'name', 
            'currency', 'date_added'
        ]
        self._portfolio = pd.DataFrame(columns=self.columns)
    
    def load_from_session(self):
        """Load portfolio data from session"""
        if 'portfolio' in session:
            portfolio_data = session['portfolio']
            self._portfolio = pd.DataFrame(portfolio_data, columns=self.columns)
        else:
            self._portfolio = pd.DataFrame(columns=self.columns)
    
    def save_to_session(self):
        """Save current portfolio state to session"""
        if hasattr(self, '_portfolio'):
            session['portfolio'] = self._portfolio.to_dict('records')
            session.modified = True
    
    def add_stock(self, stock_data):
        """Add or update stock in portfolio"""
        new_row = {
            'symbol': stock_data['symbol'],
            'quantity': stock_data['quantity'],
            'price': stock_data['price'],
            'value': stock_data['price'] * stock_data['quantity'],
            'day_return': stock_data.get('dayReturn', 0),
            'year_return': stock_data.get('yearReturn', 0),
            'name': stock_data.get('name', stock_data['symbol']),
            'currency': stock_data.get('currency', 'INR'),
            'date_added': datetime.now().isoformat()
        }
        
        # Check if stock exists
        mask = self._portfolio['symbol'] == stock_data['symbol']
        if mask.any():
            # Update existing row
            self._portfolio.loc[mask, self.columns] = list(new_row.values())
        else:
            # Append new row
            new_df = pd.DataFrame([new_row], columns=self.columns)
            self._portfolio = pd.concat([self._portfolio, new_df], ignore_index=True)
        
        self.save_to_session()
    
    def remove_stock(self, symbol):
        """Remove stock from portfolio"""
        self._portfolio = self._portfolio[
            self._portfolio['symbol'] != symbol
        ].reset_index(drop=True)
        self.save_to_session()  # Save changes to session
    
    def get_portfolio(self):
        """Get current portfolio with clean data"""
        if hasattr(self, '_portfolio') and not self._portfolio.empty:
            # Ensure all data is clean and serializable
            clean_portfolio = self._portfolio.copy()
            
            # Convert any potential problematic columns
            for col in clean_portfolio.columns:
                if clean_portfolio[col].dtype == 'object':
                    clean_portfolio[col] = clean_portfolio[col].astype(str)
                elif pd.api.types.is_numeric_dtype(clean_portfolio[col]):
                    clean_portfolio[col] = pd.to_numeric(clean_portfolio[col], errors='coerce').fillna(0)
            
            return clean_portfolio
        else:
            return pd.DataFrame(columns=self.columns)
    
    def get_total_value(self):
        """Get total portfolio value"""
        return float(self._portfolio['value'].sum())
    
    def get_returns(self):
        """Get weighted returns"""
        if self._portfolio.empty:
            return 0.0, 0.0
            
        total_value = self.get_total_value()
        if total_value == 0:
            return 0.0, 0.0
            
        weights = self._portfolio['value'] / total_value
        day_return = (weights * self._portfolio['day_return']).sum()
        year_return = (weights * self._portfolio['year_return']).sum()
        
        return float(day_return), float(year_return)

# Create global instance
portfolio_store = PortfolioDataStore()