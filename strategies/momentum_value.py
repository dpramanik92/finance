import pandas as pd
import yfinance as yf
import numpy as np
import datetime

class momentum:
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = pd.DataFrame()
        self.df['Close'] = yf.download(ticker)['Close']
        self.df['Returns'] = self.df['Close'].pct_change()
        self.df['Momentum'] = self.df['Returns'].rolling(window=20).mean()

class value:
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = pd.DataFrame()
        self.df['Close'] = yf.download(ticker)['Close']
        self.df['Returns'] = self.df['Close'].pct_change()
        self.df['Value'] = self.df['Close'] / self.df['Close'].rolling(window=20).mean()