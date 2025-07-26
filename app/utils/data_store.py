import pandas as pd
from datetime import datetime

class PortfolioDataStore:
    def __init__(self):
        self.portfolio_df = pd.DataFrame(
            columns=['symbol', 'quantity', 'price', 'value', 
                    'day_return', 'year_return', 'date_added']
        )
        
    def add_stock(self, stock_data):
        """Add or update stock in portfolio"""
        new_row = {
            'symbol': stock_data['symbol'],
            'quantity': stock_data['quantity'],
            'price': stock_data['price'],
            'value': stock_data['price'] * stock_data['quantity'],
            'day_return': stock_data.get('dayReturn', 0),
            'year_return': stock_data.get('yearReturn', 0),
            'date_added': datetime.now()
        }
        
        # Update if exists, append if new
        if stock_data['symbol'] in self.portfolio_df['symbol'].values:
            self.portfolio_df.loc[
                self.portfolio_df['symbol'] == stock_data['symbol']
            ] = pd.Series(new_row)
        else:
            self.portfolio_df = pd.concat([
                self.portfolio_df, 
                pd.DataFrame([new_row])
            ], ignore_index=True)
    
    def remove_stock(self, symbol):
        """Remove stock from portfolio"""
        self.portfolio_df = self.portfolio_df[
            self.portfolio_df['symbol'] != symbol
        ].reset_index(drop=True)
    
    def get_portfolio(self):
        """Get current portfolio"""
        return self.portfolio_df.copy()
    
    def get_total_value(self):
        """Get total portfolio value"""
        return self.portfolio_df['value'].sum()
    
    def get_returns(self):
        """Get weighted returns"""
        total_value = self.get_total_value()
        if total_value == 0:
            return 0, 0
            
        weights = self.portfolio_df['value'] / total_value
        day_return = (weights * self.portfolio_df['day_return']).sum()
        year_return = (weights * self.portfolio_df['year_return']).sum()
        
        return day_return, year_return

# Create global instance
portfolio_store = PortfolioDataStore()