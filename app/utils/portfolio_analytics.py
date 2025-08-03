import pandas as pd
import numpy as np

class PortfolioAnalytics:
    @staticmethod
    def calculate_metrics(portfolio_df):
        if portfolio_df.empty:
            return {
                'total_value': 0,
                'asset_count': 0,
                'risk_level': 'N/A',
                'diversification_score': 0,
                'largest_holding': None,
                'largest_holding_pct': 0
            }
        
        total_value = portfolio_df['value'].sum()
        
        # Calculate portfolio metrics
        metrics = {
            'total_value': total_value,
            'asset_count': len(portfolio_df),
            'asset_distribution': {},
            'risk_metrics': {}
        }
        
        # Calculate percentage allocation
        portfolio_df['allocation'] = portfolio_df['value'] / total_value * 100
        
        # Determine risk level based on concentration
        max_allocation = portfolio_df['allocation'].max()
        if max_allocation > 30:
            risk_level = 'High'
        elif max_allocation > 20:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
            
        # Calculate diversification score (0-100)
        ideal_allocation = 100 / len(portfolio_df)
        allocation_deviation = np.abs(portfolio_df['allocation'] - ideal_allocation).mean()
        diversification_score = max(0, 100 - allocation_deviation)
        
        # Get largest holding
        largest_holding = portfolio_df.loc[portfolio_df['allocation'].idxmax()]
        
        metrics.update({
            'risk_level': risk_level,
            'diversification_score': round(diversification_score, 2),
            'largest_holding': largest_holding['symbol'],
            'largest_holding_pct': round(max_allocation, 2)
        })
        
        return metrics