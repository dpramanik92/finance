import pandas as pd
import numpy as np
from portfolio.levPortfolio import levPortfolio
from strategies.utils import EmceeMCMC, gaussian_prior
from strategies.linreg import LinearRegressionLikelihood

def main():
    # Example usage of levPortfolio
    returns = pd.DataFrame({
        'x1': np.random.normal(0.01, 0.02, 100),
        'x2': np.random.normal(0.01, 0.02, 100)
    })
    rate = 0.05
    portfolio = levPortfolio(returns, rate)

    equity = 100000
    borrow = 50000
    characteristics = portfolio.calculate_characteristics(equity, borrow)
    print("Characteristics:", characteristics)

    # Example usage of EmceeMCMC and gaussian_prior
    mcmc = EmceeMCMC()
    prior = gaussian_prior(mu=0, sigma=1)
    print("Gaussian Prior:", prior)

if __name__ == "__main__":
    main()
# This script serves as an entry point for the portfolio analysis package.
# It demonstrates the usage of the levPortfolio class and MCMC sampling utilities.
