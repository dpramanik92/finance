import json
import numpy as np
from datetime import datetime
from flask import Blueprint, render_template, jsonify
from ..utils.portfolio_analytics import PortfolioAnalytics
from ..utils.data_store import portfolio_store
from ..utils.performance_analytics import PerformanceAnalytics

main = Blueprint('main', __name__, template_folder='../templates')

# Create blueprint for main routes
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/portfolio')
def portfolio():
    try:
        portfolio_df = portfolio_store.get_portfolio()
        
        # Initialize analytics with safe defaults
        analytics = {
            'total_value': 0.0,
            'asset_count': 0,
            'risk_level': 'N/A',
            'diversification_score': 0.0,
            'largest_holding': 'None',
            'largest_holding_pct': 0.0
        }
        
        # Calculate analytics if portfolio exists
        if not portfolio_df.empty:
            total_value = float(portfolio_df['value'].sum())
            analytics.update({
                'total_value': total_value,
                'asset_count': len(portfolio_df),
                'risk_level': 'Low',
                'diversification_score': 100.0,
                'largest_holding': str(portfolio_df.loc[portfolio_df['value'].idxmax(), 'symbol']),
                'largest_holding_pct': float((portfolio_df['value'].max() / total_value) * 100)
            })
        
        # Get performance data with safe conversion
        try:
            perf = PerformanceAnalytics()
            raw_performance = perf.get_portfolio_returns(portfolio_df)
            
            # Ensure all values are JSON serializable
            performance_data = {
                'portfolio_hist': {
                    'index': [str(x) for x in raw_performance['portfolio_hist']['index']],
                    'values': [float(x) for x in raw_performance['portfolio_hist']['values']]
                },
                'benchmark_hist': {
                    'index': [str(x) for x in raw_performance['benchmark_hist']['index']],
                    'values': [float(x) for x in raw_performance['benchmark_hist']['values']]
                },
                'metrics': {
                    'one_year_return': float(raw_performance['metrics'].get('one_year_return', 0)),
                    'volatility': float(raw_performance['metrics'].get('volatility', 0))
                }
            }
        except Exception as e:
            print(f"Performance calculation error: {e}")
            performance_data = {
                'portfolio_hist': {'index': [], 'values': []},
                'benchmark_hist': {'index': [], 'values': []},
                'metrics': {'one_year_return': 0.0, 'volatility': 0.0}
            }
        
        # Convert portfolio to list of dicts with safe conversion
        portfolio_list = []
        if not portfolio_df.empty:
            for _, row in portfolio_df.iterrows():
                try:
                    portfolio_list.append({
                        'symbol': str(row['symbol']),
                        'name': str(row.get('name', '')),
                        'quantity': int(row['quantity']),
                        'price': float(row['price']),
                        'value': float(row['value']),
                        'allocation': float(row['value'] / total_value * 100),
                        'day_return': float(row.get('day_return', 0)),
                        'year_return': float(row.get('year_return', 0))
                    })
                except Exception as e:
                    print(f"Error converting row {row['symbol']}: {e}")
                    continue
        
        # Verify all data is JSON serializable before rendering
        try:
            json.dumps({
                'analytics': analytics,
                'portfolio': portfolio_list,
                'performance': performance_data
            })
        except TypeError as e:
            print(f"JSON serialization error: {e}")
            raise
            
        return render_template(
            'portfolio.html',
            analytics=analytics,
            portfolio=portfolio_list,
            performance=performance_data
        )
        
    except Exception as e:
        print(f"Portfolio error: {str(e)}")
        # Return safe default values
        return render_template(
            'portfolio.html',
            analytics={'total_value': 0.0, 'asset_count': 0},
            portfolio=[],
            performance={
                'portfolio_hist': {'index': [], 'values': []},
                'benchmark_hist': {'index': [], 'values': []},
                'metrics': {'one_year_return': 0.0, 'volatility': 0.0}
            }
        )

@main.route('/strategies')
def strategies():
    return render_template('strategies.html')

@main.route('/analysis')
def analysis():
    return render_template('analysis.html')

@main.route('/settings')
def settings():
    return render_template('settings.html')

@main.route('/about')
def about():
    return render_template('about.html')
