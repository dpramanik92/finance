import pandas as pd
import numpy as np

class levPortfolio:
    def __init__(self, returns, rate):
        self.returns = returns.copy()
        self.rate = rate  # Store the rate for potential future use
        self.mu1 = self.returns['x1'].mean()
        self.mu2 = self.returns['x2'].mean()
        self.sigma1 = self.returns['x1'].std()
        self.sigma2 = self.returns['x2'].std()
        self.rho = self.returns['x1'].corr(self.returns['x2'])
        
    def calculate_characteristics(self, equity, borrow):
        long = equity + borrow
        short = borrow
        net_capital = long - short
        gross_capital = long + short
        
        if long != short:
            leverage = gross_capital/net_capital
            w1 = long/net_capital
            w2 = short/net_capital
        else:
            leverage = np.inf
            w1 = w2 = 1
            
        ret = w1*self.mu1 - w2*self.mu2
        variance = (w1**2 * self.sigma1**2) + (w2**2 * self.sigma2**2) - (2 * w1 * w2 * self.rho * self.sigma1 * self.sigma2)
        sharpe = (ret-self.rate)/np.sqrt(variance)
        
        return ret, np.sqrt(variance), sharpe, leverage, w1, w2

    def efficiency(self, w):
        w1 = w
        w2 = 1-w
        ret = w1*self.mu1 + w2*self.mu2
            
        variance = (w1**2 * self.sigma1**2) + (w2**2 * self.sigma2**2) + (2 * w1 * w2 * self.rho * self.sigma1 * self.sigma2)
        sharpe = (ret-self.rate)/np.sqrt(variance)  # Now using self.rate instead of hardcoded 0.05

        return ret, np.sqrt(variance), sharpe
