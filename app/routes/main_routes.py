import json
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, jsonify
from ..utils.portfolio_analytics import PortfolioAnalytics
from ..utils.data_store import portfolio_store
from ..utils.performance_analytics import PerformanceAnalytics

main = Blueprint('main', __name__, template_folder='../templates')

# Create blueprint for main routes
main = Blueprint('main', __name__)

@main.before_request
def load_portfolio_data():
    """Load portfolio data from session before each request"""
    portfolio_store.load_from_session()

@main.route('/')
def home():
    # Load existing portfolio data from session
    portfolio_store.load_from_session()
    return render_template('index.html')

@main.route('/portfolio')
def portfolio():
    try:
        # Ensure portfolio data is loaded from session
        portfolio_store.load_from_session()
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
            portfolio_df_clean = portfolio_df.reset_index(drop=True)
            total_value = float(portfolio_df_clean['value'].sum())
            
            for idx in range(len(portfolio_df_clean)):
                try:
                    row = portfolio_df_clean.iloc[idx]
                    portfolio_item = {
                        'symbol': str(row['symbol']) if pd.notna(row['symbol']) else '',
                        'name': str(row.get('name', '')) if pd.notna(row.get('name', '')) else '',
                        'quantity': int(float(row['quantity'])) if pd.notna(row['quantity']) else 0,
                        'price': float(row['price']) if pd.notna(row['price']) else 0.0,
                        'value': float(row['value']) if pd.notna(row['value']) else 0.0,
                        'allocation': float(row['value'] / total_value * 100) if total_value > 0 and pd.notna(row['value']) else 0.0,
                        'day_return': float(row.get('day_return', 0)) if pd.notna(row.get('day_return', 0)) else 0.0,
                        'year_return': float(row.get('year_return', 0)) if pd.notna(row.get('year_return', 0)) else 0.0
                    }
                    portfolio_list.append(portfolio_item)
                except Exception as e:
                    print(f"Error converting row {idx}: {e}")
                    continue
        
        # Convert everything to basic Python types (not strings) for JSON safety
        def make_json_safe(obj):
            """Convert to JSON-safe types while preserving data types"""
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, dict):
                return {str(k): make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_json_safe(item) for item in obj]
            elif hasattr(obj, '__call__'):  # Functions/methods
                return None
            elif hasattr(obj, 'tolist'):  # numpy arrays
                return make_json_safe(obj.tolist())
            elif pd.isna(obj):
                return None
            else:
                try:
                    # Try to convert to basic type
                    if hasattr(obj, 'item'):  # numpy scalars
                        return obj.item()
                    else:
                        return str(obj)
                except Exception:
                    return None
        
        # Make data JSON-safe while preserving types
        analytics_safe = make_json_safe(analytics)
        portfolio_safe = make_json_safe(portfolio_list)
        performance_safe = make_json_safe(performance_data)
        
        # Test JSON serialization
        try:
            json.dumps({
                'analytics': analytics_safe,
                'portfolio': portfolio_safe,
                'performance': performance_safe
            })
            print("JSON serialization successful!")
        except Exception as e:
            print(f"Still failing JSON serialization: {e}")
            # Fallback to string conversion
            analytics_safe = {k: str(v) for k, v in analytics.items()}
            portfolio_safe = [{k: str(v) for k, v in item.items()} for item in portfolio_list]
            performance_safe = {
                'portfolio_hist': {
                    'index': [str(x) for x in performance_data['portfolio_hist']['index']],
                    'values': [str(x) for x in performance_data['portfolio_hist']['values']]
                },
                'benchmark_hist': {
                    'index': [str(x) for x in performance_data['benchmark_hist']['index']],
                    'values': [str(x) for x in performance_data['benchmark_hist']['values']]
                },
                'metrics': {k: str(v) for k, v in performance_data['metrics'].items()}
            }
            
        return render_template(
            'portfolio.html',
            analytics=analytics_safe,
            portfolio=portfolio_safe,
            performance=performance_safe
        )
        
    except Exception as e:
        print(f"Portfolio error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return safe default values
        return render_template(
            'portfolio.html',
            analytics={
                'total_value': 0.0,
                'asset_count': 0,
                'risk_level': 'N/A',
                'diversification_score': 0.0,
                'largest_holding': 'None',
                'largest_holding_pct': 0.0
            },
            portfolio=[],
            performance={
                'portfolio_hist': {'index': [], 'values': []},
                'benchmark_hist': {'index': [], 'values': []},
                'metrics': {'one_year_return': 0.0, 'volatility': 0.0}
            }
        )

@main.route('/analysis')
def analysis():
    return render_template('analysis.html')

@main.route('/risk_metrics')
def risk_metrics():
    return render_template('risk_metrics.html')

@main.route('/broad_market')
def broad_market():
    return render_template('broad_market.html')

@main.route('/about')
def about():
    return render_template('about.html')
