import pandas as pd
import numpy as np
from levPortfolio import levPortfolio

def print_versions():
    """Print versions of key dependencies."""
    print("Pandas version:", pd.__version__)
    print("NumPy version:", np.__version__)

def generate_sample_data(mean1=0.12, mean2=0.04, sd1=0.12, sd2=0.12, 
                        rho=0.9, n_samples=1000):
    """Generate sample return data with specified parameters.
    
    Args:
        mean1 (float): Mean return for first asset
        mean2 (float): Mean return for second asset
        sd1 (float): Standard deviation for first asset
        sd2 (float): Standard deviation for second asset
        rho (float): Correlation coefficient between assets
        n_samples (int): Number of samples to generate
        
    Returns:
        pd.DataFrame: DataFrame with generated return data
    """
    mean = [mean1, mean2]
    cov = [[sd1**2, rho*sd1*sd2],
           [rho*sd1*sd2, sd2**2]]
    
    data = np.random.multivariate_normal(mean, cov, size=n_samples)
    return pd.DataFrame(data, columns=['x1', 'x2'])

def print_portfolio_stats(characteristics):
    """Print portfolio statistics in a formatted way."""
    ret, vol, sharpe, lev, w1, w2 = characteristics
    
    print("\nPortfolio Characteristics:")
    print(f"{'Return:':<15} {ret:.4f}")
    print(f"{'Volatility:':<15} {vol:.4f}")
    print(f"{'Sharpe Ratio:':<15} {sharpe:.4f}")
    print(f"{'Leverage:':<15} {lev:.2f}")
    print(f"{'Weights:':<15} w1 = {w1:.2f}, w2 = {w2:.2f}")

def main():
    """Main execution function."""
    # Print dependency versions
    print_versions()
    
    # Generate sample data with default parameters
    df = generate_sample_data()
    
    # Or specify custom parameters
    # df = generate_sample_data(
    #     mean1=0.15, mean2=0.05,
    #     sd1=0.20, sd2=0.10,
    #     rho=0.5,
    #     n_samples=2000
    # )
    
    print("\nData Statistics:")
    print(df.describe())
    print("\nCorrelation Matrix:")
    print(df.corr())
    
    # Create and analyze portfolio
    risk_free_rate = 0.04
    port = levPortfolio(df, risk_free_rate)
    
    # Calculate portfolio characteristics
    portfolio_characteristics = port.calculate_characteristics(100, 50)
    print_portfolio_stats(portfolio_characteristics)

if __name__ == "__main__":
    main()

