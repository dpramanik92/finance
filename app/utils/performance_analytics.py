import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class PerformanceAnalytics:
    def __init__(self):
        self.risk_free_rate = 0.0725  # 7.25% (10-year Indian govt bond yield)
        self.benchmark = '^NSEI'  # NIFTY 50 index
        self.initial_value = 100000  # Starting value of 1 lakh

    def get_benchmark_day_return(self):
        """Get NIFTY 50 1-day return percentage"""
        try:
            print("Fetching NIFTY 50 day return...")
            nifty = yf.Ticker('^NSEI')
            hist = nifty.history(period='5d')  # Get more days to ensure we have data
            
            if len(hist) >= 2:
                today_close = float(hist['Close'].iloc[-1])
                yesterday_close = float(hist['Close'].iloc[-2])
                day_return = ((today_close - yesterday_close) / yesterday_close) * 100
                print(f"NIFTY day return: {day_return:.2f}%")
                return float(day_return)
            else:
                print("Not enough NIFTY data available")
                return 0.0
        except Exception as e:
            print(f"Error getting benchmark day return: {e}")
            return 0.0

    def calculate_max_drawdown(self, values):
        """Calculate maximum drawdown from a series of values"""
        try:
            if len(values) < 2:
                return 0.0
            
            # Convert to numpy array for easier calculation
            values = np.array(values)
            
            # Calculate running maximum (peak values)
            running_max = np.maximum.accumulate(values)
            
            # Calculate drawdown at each point
            drawdown = (values - running_max) / running_max
            
            # Maximum drawdown is the minimum (most negative) drawdown
            max_drawdown = np.min(drawdown) * 100  # Convert to percentage
            
            return float(max_drawdown)
            
        except Exception as e:
            print(f"Error calculating max drawdown: {e}")
            return 0.0

    def calculate_portfolio_beta(self, portfolio_returns, benchmark_returns):
        """Calculate portfolio beta relative to benchmark"""
        try:
            if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
                return 1.0
            
            # Calculate correlation and standard deviations
            correlation = np.corrcoef(portfolio_returns, benchmark_returns)[0, 1]
            portfolio_std = np.std(portfolio_returns)
            benchmark_std = np.std(benchmark_returns)
            
            # Beta = correlation * (portfolio_std / benchmark_std)
            if benchmark_std > 0:
                beta = correlation * (portfolio_std / benchmark_std)
                return float(beta)
            else:
                return 1.0
                
        except Exception as e:
            print(f"Error calculating beta: {e}")
            return 1.0

    def calculate_value_at_risk(self, returns, portfolio_value, confidence_level=0.01):
        """Calculate Value at Risk (VaR) at 99% confidence level (1% tail risk)"""
        try:
            if len(returns) < 2:
                return {'var_percent': 0.0, 'var_value': 0.0}
            
            # Sort returns in ascending order
            sorted_returns = np.sort(returns)
            
            # Find the percentile corresponding to the confidence level (1% for 99% confidence)
            var_index = int(confidence_level * len(sorted_returns))
            var_percent = sorted_returns[var_index] * 100  # Convert to percentage
            
            # Calculate VaR in value terms
            var_value = portfolio_value * sorted_returns[var_index]  # Actual currency loss
            
            return {
                'var_percent': float(var_percent),
                'var_value': float(var_value)
            }
            
        except Exception as e:
            print(f"Error calculating VaR: {e}")
            return {'var_percent': 0.0, 'var_value': 0.0}

    def get_portfolio_returns(self, portfolio_df):
        print(portfolio_df)
        try:
            if portfolio_df.empty:
                return self._get_empty_data()

            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)

            # Get NIFTY 50 benchmark data first
            nifty = yf.Ticker('^NSEI')
            nifty_data = nifty.history(start=start_date, end=end_date)
            
            if nifty_data.empty:
                return self._get_empty_data()

            # Calculate benchmark returns for imputation
            nifty_returns = nifty_data['Close'].pct_change().fillna(0)

            # Get portfolio stock data with imputation
            portfolio_stocks = {}
            for _, row in portfolio_df.iterrows():
                symbol = row['symbol']
                weight = row['value'] / portfolio_df['value'].sum()  # Portfolio weight
                try:
                    stock = yf.Ticker(symbol)
                    stock_data = stock.history(start=start_date, end=end_date)
                    
                    if not stock_data.empty:
                        # Align stock data with benchmark dates and impute missing values
                        stock_data_aligned = self._align_and_impute_data(
                            stock_data, nifty_data, nifty_returns, symbol
                        )
                        portfolio_stocks[symbol] = {
                            'data': stock_data_aligned,
                            'weight': weight
                        }
                    else:
                        # If no stock data available, create synthetic data using benchmark
                        print(f"No data for {symbol}, using benchmark as proxy")
                        synthetic_data = self._create_synthetic_data(nifty_data, symbol)
                        portfolio_stocks[symbol] = {
                            'data': synthetic_data,
                            'weight': weight
                        }
                except Exception as e:
                    print(f"Error getting data for {symbol}: {e}")
                    # Create synthetic data using benchmark as fallback
                    synthetic_data = self._create_synthetic_data(nifty_data, symbol)
                    portfolio_stocks[symbol] = {
                        'data': synthetic_data,
                        'weight': weight
                    }

            # Calculate portfolio and benchmark values for each date
            portfolio_values = []
            benchmark_values = []
            dates = []
            
            # Get initial prices for normalization
            initial_nifty_price = nifty_data['Close'].iloc[0]
            
            for i, date in enumerate(nifty_data.index):
                dates.append(date.strftime('%Y-%m-%d'))
                
                # Calculate portfolio value on this date
                portfolio_value = 0.0
                total_weight = 0.0
                
                for symbol, stock_info in portfolio_stocks.items():
                    stock_data = stock_info['data']
                    weight = stock_info['weight']
                    
                    # Get stock price on this date
                    if date in stock_data.index:
                        # Calculate return from initial price
                        initial_stock_price = stock_data['Close'].iloc[0]
                        current_stock_price = stock_data.loc[date, 'Close']
                        stock_return = (current_stock_price / initial_stock_price) - 1
                        
                        # Add weighted contribution to portfolio
                        portfolio_value += self.initial_value * (1 + stock_return) * weight
                        total_weight += weight
                
                # Normalize if we don't have complete weight coverage
                if total_weight > 0 and total_weight != 1.0:
                    portfolio_value = self.initial_value + (portfolio_value - self.initial_value) * (1 / total_weight)
                elif total_weight == 0:
                    portfolio_value = self.initial_value
                
                portfolio_values.append(float(portfolio_value))
                
                # Calculate benchmark value (NIFTY 50)
                current_nifty_price = nifty_data['Close'].iloc[i]
                nifty_return = (current_nifty_price / initial_nifty_price) - 1
                benchmark_value = self.initial_value * (1 + nifty_return)
                benchmark_values.append(float(benchmark_value))

            # Calculate performance metrics including max drawdown
            metrics = self._calculate_performance_metrics(portfolio_values, benchmark_values)

            return {
                'portfolio_hist': {
                    'index': dates,
                    'values': portfolio_values
                },
                'benchmark_hist': {
                    'index': dates,
                    'values': benchmark_values
                },
                'metrics': metrics
            }
        except Exception as e:
            print(f"Error in performance analytics: {e}")
            return self._get_empty_data()

    def _align_and_impute_data(self, stock_data, benchmark_data, benchmark_returns, symbol):
        """Align stock data with benchmark and impute missing values using benchmark returns"""
        try:
            # Reindex stock data to match benchmark dates
            stock_aligned = stock_data.reindex(benchmark_data.index)
            
            # Forward fill first to handle gaps
            stock_aligned['Close'] = stock_aligned['Close'].fillna(method='ffill')
            
            # Calculate stock returns
            stock_returns = stock_aligned['Close'].pct_change()
            
            # Find missing data points
            missing_mask = stock_aligned['Close'].isna()
            
            if missing_mask.any():
                print(f"Imputing {missing_mask.sum()} missing data points for {symbol}")
                
                # Get the last known price before missing data
                last_known_price = None
                imputed_prices = stock_aligned['Close'].copy()
                
                for i, (date, is_missing) in enumerate(missing_mask.items()):
                    if is_missing:
                        if last_known_price is None:
                            # If missing from the start, use benchmark initial price scaled
                            if i > 0:
                                # Use previous benchmark return to estimate
                                benchmark_return = benchmark_returns.iloc[i]
                                prev_price = imputed_prices.iloc[i-1]
                                if pd.notna(prev_price):
                                    # Apply benchmark return to last known price
                                    imputed_prices.iloc[i] = prev_price * (1 + benchmark_return)
                                else:
                                    # Use benchmark price as proxy
                                    imputed_prices.iloc[i] = benchmark_data['Close'].iloc[i]
                            else:
                                imputed_prices.iloc[i] = benchmark_data['Close'].iloc[i]
                        else:
                            # Use benchmark return to estimate missing price
                            benchmark_return = benchmark_returns.iloc[i]
                            imputed_prices.iloc[i] = last_known_price * (1 + benchmark_return)
                    else:
                        last_known_price = imputed_prices.iloc[i]
                
                stock_aligned['Close'] = imputed_prices
                
                # Recalculate other OHLV data based on Close price
                for col in ['Open', 'High', 'Low']:
                    if col in stock_aligned.columns:
                        stock_aligned[col] = stock_aligned[col].fillna(stock_aligned['Close'])
                
                if 'Volume' in stock_aligned.columns:
                    # Use median volume for missing volume data
                    median_volume = stock_aligned['Volume'].median()
                    stock_aligned['Volume'] = stock_aligned['Volume'].fillna(median_volume)
            
            return stock_aligned
            
        except Exception as e:
            print(f"Error in data alignment for {symbol}: {e}")
            return stock_data

    def _create_synthetic_data(self, benchmark_data, symbol):
        """Create synthetic stock data using benchmark as a proxy"""
        try:
            synthetic_data = benchmark_data.copy()
            
            # Add some random variation to differentiate from pure benchmark
            # This simulates stock-specific risk while maintaining market correlation
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed based on symbol
            
            # Generate random factors (mean 1, small standard deviation)
            random_factors = np.random.normal(1, 0.1, len(benchmark_data))
            
            # Apply random factors to create stock-specific variation
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in synthetic_data.columns:
                    synthetic_data[col] = synthetic_data[col] * random_factors
            
            # Keep volume similar to benchmark but with variation
            if 'Volume' in synthetic_data.columns:
                volume_factors = np.random.normal(1, 0.3, len(benchmark_data))
                synthetic_data['Volume'] = synthetic_data['Volume'] * np.abs(volume_factors)
            
            print(f"Created synthetic data for {symbol} based on benchmark")
            return synthetic_data
            
        except Exception as e:
            print(f"Error creating synthetic data for {symbol}: {e}")
            return benchmark_data.copy()

    def _calculate_performance_metrics(self, portfolio_values, benchmark_values):
        """Calculate performance metrics from value series including VaR at 99% confidence"""
        try:
            if len(portfolio_values) > 1:
                portfolio_returns = [(portfolio_values[i] / portfolio_values[i-1]) - 1 
                                   for i in range(1, len(portfolio_values))]
                benchmark_returns = [(benchmark_values[i] / benchmark_values[i-1]) - 1 
                                   for i in range(1, len(benchmark_values))]
                
                # Get current portfolio value
                current_portfolio_value = portfolio_values[-1]
                
                # Calculate maximum drawdown
                max_drawdown = self.calculate_max_drawdown(portfolio_values)
                
                # Calculate portfolio beta
                portfolio_beta = self.calculate_portfolio_beta(portfolio_returns, benchmark_returns)
                
                # Calculate Value at Risk (99% confidence) in both percentage and value terms
                var_results = self.calculate_value_at_risk(portfolio_returns, current_portfolio_value, 0.01)
                
                # Calculate correlation with benchmark
                correlation = 0.0
                if len(portfolio_returns) == len(benchmark_returns) and len(portfolio_returns) > 1:
                    correlation = float(np.corrcoef(portfolio_returns, benchmark_returns)[0, 1])
                
                # Calculate 1 year return
                if len(portfolio_values) >= 252:
                    one_year_return = float(((portfolio_values[-1] / portfolio_values[-252]) - 1) * 100)
                    last_year_returns = portfolio_returns[-251:]
                    daily_volatility = np.std(last_year_returns)
                    portfolio_volatility = float(daily_volatility * np.sqrt(252) * 100)
                    
                    # Calculate Sharpe ratio
                    daily_excess_returns = [r - (self.risk_free_rate / 252) for r in last_year_returns]
                    mean_excess_return = np.mean(daily_excess_returns)
                    std_excess_return = np.std(daily_excess_returns)
                    
                    sharpe_ratio = float((mean_excess_return / std_excess_return) * np.sqrt(252)) if std_excess_return > 0 else 0.0
                    
                else:
                    # Annualize returns for shorter periods
                    total_days = len(portfolio_values) - 1
                    one_year_return = float(((portfolio_values[-1] / portfolio_values[0]) - 1) * 100)
                    
                    if total_days > 0:
                        years = total_days / 252.0
                        annualized_return = float(((portfolio_values[-1] / portfolio_values[0]) ** (1/years) - 1) * 100)
                        one_year_return = annualized_return
                    
                    daily_volatility = np.std(portfolio_returns)
                    portfolio_volatility = float(daily_volatility * np.sqrt(252) * 100)
                    
                    daily_excess_returns = [r - (self.risk_free_rate / 252) for r in portfolio_returns]
                    mean_excess_return = np.mean(daily_excess_returns)
                    std_excess_return = np.std(daily_excess_returns)
                    
                    sharpe_ratio = float((mean_excess_return / std_excess_return) * np.sqrt(252)) if std_excess_return > 0 else 0.0
                    
            else:
                portfolio_volatility = 0.0
                one_year_return = 0.0
                sharpe_ratio = 0.0
                max_drawdown = 0.0
                portfolio_beta = 1.0
                var_results = {'var_percent': 0.0, 'var_value': 0.0}
                correlation = 0.0

            return {
                'one_year_return': one_year_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'beta': portfolio_beta,
                'var_99_percent': var_results['var_percent'],  # Changed from var_95_percent
                'var_99_value': var_results['var_value'],      # Changed from var_95_value
                'correlation': correlation
            }
        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return {
                'one_year_return': 0.0, 
                'volatility': 0.0, 
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'beta': 1.0,
                'var_99_percent': 0.0,  # Changed from var_95_percent
                'var_99_value': 0.0,    # Changed from var_95_value
                'correlation': 0.0
            }

    def _get_empty_data(self):
        return {
            'portfolio_hist': {'index': [], 'values': []},
            'benchmark_hist': {'index': [], 'values': []},
            'metrics': {
                'one_year_return': 0.0, 
                'volatility': 0.0, 
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'beta': 1.0,
                'var_99_percent': 0.0,  # Changed from var_95_percent
                'var_99_value': 0.0,    # Changed from var_95_value
                'correlation': 0.0
            }
        }