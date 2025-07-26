import numpy as np
import statsmodels.api as sm
from scipy.stats import norm

class LinearRegressionLikelihood:
    def __init__(self):
        self.model = None
        self.results = None
        self.sigma = None
    
    def fit(self, X, y):
        """
        Fit the linear regression model using statsmodels
        X: numpy array of shape (n_samples, n_features)
        y: numpy array of shape (n_samples,)
        """
        # Add constant term for intercept
        X_with_intercept = sm.add_constant(X)
        
        # Fit the model using OLS
        self.model = sm.OLS(y, X_with_intercept)
        self.results = self.model.fit()
        
        # Get sigma (standard deviation of residuals)
        self.sigma = np.sqrt(self.results.mse_resid)
    
    def predict(self, X):
        """
        Make predictions
        X: numpy array of shape (n_samples, n_features)
        """
        if self.results is None:
            raise ValueError("Model must be fitted before making predictions")
            
        X_with_intercept = sm.add_constant(X)
        return self.results.predict(X_with_intercept)
    
    def log_likelihood(self, X, y):
        """
        Calculate log likelihood of the data given the model
        Returns sum of log probabilities
        """
        if self.results is None:
            raise ValueError("Model must be fitted before calculating likelihood")
        
        y_pred = self.predict(X)
        log_probs = norm.logpdf(y, loc=y_pred, scale=self.sigma)
        return np.sum(log_probs)
    
    def likelihood(self, X, y):
        """
        Calculate likelihood of the data given the model
        Returns product of probabilities
        """
        return np.exp(self.log_likelihood(X, y))