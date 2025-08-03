import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class PerformanceAnalytics:
    def __init__(self):
        self.risk_free_rate = 0.0725  # 7.25% (10-year Indian govt bond yield)
        self.benchmark = '^NSEI'  # NIFTY 50 index

    def get_portfolio_returns(self, portfolio_df):
        try:
            if portfolio_df.empty:
                return self._get_empty_data()

            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)

            # Get NIFTY 50 data
            nifty = yf.Ticker('^NSEI')
            nifty_data = nifty.history(start=start_date, end=end_date)
            
            if nifty_data.empty:
                return self._get_empty_data()

            # Calculate portfolio returns
            total_value = portfolio_df['value'].sum()
            portfolio_returns = []
            dates = []

            for date in nifty_data.index:
                dates.append(date.strftime('%Y-%m-%d'))
                portfolio_returns.append(float(np.random.uniform(-1, 1)))  # Placeholder for now

            # Calculate metrics
            volatility = float(np.std(portfolio_returns) * np.sqrt(252))
            one_year_return = float(np.mean(portfolio_returns[-252:]) * 252)

            return {
                'portfolio_hist': {
                    'index': dates,
                    'values': [float(x * 100) for x in portfolio_returns]
                },
                'benchmark_hist': {
                    'index': dates,
                    'values': [float(x * 100) for x in nifty_data['Close'].pct_change().fillna(0).cumsum()]
                },
                'metrics': {
                    'one_year_return': one_year_return,
                    'volatility': volatility
                }
            }
        except Exception as e:
            print(f"Error in performance analytics: {e}")
            return self._get_empty_data()

    def _get_empty_data(self):
        return {
            'portfolio_hist': {'index': [], 'values': []},
            'benchmark_hist': {'index': [], 'values': []},
            'metrics': {'one_year_return': 0.0, 'volatility': 0.0}
        }