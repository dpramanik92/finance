import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class PerformanceAnalytics:
    def __init__(self):
        self.risk_free_rate = 0.0725  # 7.25% (10-year Indian govt bond yield)
        self.benchmark = '^NSEI'  # NIFTY 50 index
        self.initial_value = 100000  # Starting value of 1 lakh

    def get_portfolio_returns(self, portfolio_df):
        print(portfolio_df)
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

            # Get portfolio stock data
            portfolio_values = []
            benchmark_values = []
            dates = []
            
            # Get historical data for all stocks in portfolio
            portfolio_stocks = {}
            for _, row in portfolio_df.iterrows():
                symbol = row['symbol']
                weight = row['value'] / portfolio_df['value'].sum()  # Portfolio weight
                try:
                    stock = yf.Ticker(symbol)
                    stock_data = stock.history(start=start_date, end=end_date)
                    if not stock_data.empty:
                        portfolio_stocks[symbol] = {
                            'data': stock_data,
                            'weight': weight
                        }
                except Exception as e:
                    print(f"Error getting data for {symbol}: {e}")
                    continue

            # Get initial prices for normalization
            initial_nifty_price = nifty_data['Close'].iloc[0]
            
            # Calculate portfolio and benchmark values for each date
            for i, date in enumerate(nifty_data.index):
                dates.append(date.strftime('%Y-%m-%d'))
                
                # Calculate portfolio value on this date
                portfolio_value = self.initial_value
                total_weight = 0.0
                
                for symbol, stock_info in portfolio_stocks.items():
                    stock_data = stock_info['data']
                    weight = stock_info['weight']
                    
                    # Get stock price on this date if available
                    if date in stock_data.index:
                        # Calculate return from initial price
                        initial_stock_price = stock_data['Close'].iloc[0]
                        current_stock_price = stock_data.loc[date, 'Close']
                        stock_return = (current_stock_price / initial_stock_price) - 1
                        
                        # Add weighted contribution to portfolio
                        portfolio_value += self.initial_value * stock_return * weight
                        total_weight += weight
                
                # If we don't have complete data, use available weights
                if total_weight > 0:
                    portfolio_value = self.initial_value + (portfolio_value - self.initial_value) * (1 / total_weight if total_weight < 1 else 1)
                
                portfolio_values.append(float(portfolio_value))
                
                # Calculate benchmark value (NIFTY 50)
                current_nifty_price = nifty_data['Close'].iloc[i]
                nifty_return = (current_nifty_price / initial_nifty_price) - 1
                benchmark_value = self.initial_value * (1 + nifty_return)
                benchmark_values.append(float(benchmark_value))

            # Calculate metrics based on returns
            if len(portfolio_values) > 1:
                portfolio_returns = [(portfolio_values[i] / portfolio_values[i-1]) - 1 for i in range(1, len(portfolio_values))]
                benchmark_returns = [(benchmark_values[i] / benchmark_values[i-1]) - 1 for i in range(1, len(benchmark_values))]
                
                # Calculate 1 year return (assuming constant portfolio over last 1 year)
                if len(portfolio_values) >= 252:
                    # Use last 252 trading days for 1 year return
                    one_year_return = float(((portfolio_values[-1] / portfolio_values[-252]) - 1) * 100)
                    
                    # Calculate volatility using last 1 year daily returns
                    last_year_returns = portfolio_returns[-251:]  # Last 251 daily returns (252 values = 251 returns)
                    daily_volatility = np.std(last_year_returns)
                    portfolio_volatility = float(daily_volatility * np.sqrt(252) * 100)
                    
                    # Calculate annualized Sharpe ratio using last 1 year data
                    daily_excess_returns = [r - (self.risk_free_rate / 252) for r in last_year_returns]  # Daily risk-free rate
                    mean_excess_return = np.mean(daily_excess_returns)
                    std_excess_return = np.std(daily_excess_returns)
                    
                    if std_excess_return > 0:
                        sharpe_ratio = float((mean_excess_return / std_excess_return) * np.sqrt(252))  # Annualized Sharpe ratio
                    else:
                        sharpe_ratio = 0.0
                        
                else:
                    # If less than 1 year of data, use all available data
                    total_days = len(portfolio_values) - 1
                    one_year_return = float(((portfolio_values[-1] / portfolio_values[0]) - 1) * 100)
                    
                    # Annualize the return for comparison
                    if total_days > 0:
                        years = total_days / 252.0
                        annualized_return = float(((portfolio_values[-1] / portfolio_values[0]) ** (1/years) - 1) * 100)
                        one_year_return = annualized_return
                    
                    # Calculate volatility from all available daily returns
                    daily_volatility = np.std(portfolio_returns)
                    portfolio_volatility = float(daily_volatility * np.sqrt(252) * 100)
                    
                    # Calculate Sharpe ratio using all available data
                    daily_excess_returns = [r - (self.risk_free_rate / 252) for r in portfolio_returns]
                    mean_excess_return = np.mean(daily_excess_returns)
                    std_excess_return = np.std(daily_excess_returns)
                    
                    if std_excess_return > 0:
                        sharpe_ratio = float((mean_excess_return / std_excess_return) * np.sqrt(252))
                    else:
                        sharpe_ratio = 0.0
                        
            else:
                portfolio_volatility = 0.0
                one_year_return = 0.0
                sharpe_ratio = 0.0

            return {
                'portfolio_hist': {
                    'index': dates,
                    'values': portfolio_values
                },
                'benchmark_hist': {
                    'index': dates,
                    'values': benchmark_values
                },
                'metrics': {
                    'one_year_return': one_year_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio
                }
            }
        except Exception as e:
            print(f"Error in performance analytics: {e}")
            return self._get_empty_data()

    def _get_empty_data(self):
        return {
            'portfolio_hist': {'index': [], 'values': []},
            'benchmark_hist': {'index': [], 'values': []},
            'metrics': {'one_year_return': 0.0, 'volatility': 0.0, 'sharpe_ratio': 0.0}
        }