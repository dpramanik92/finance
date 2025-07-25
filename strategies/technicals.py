
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
import mplfinance as mpf
import ta
import datetime

def percent_rank(window):
    x = window[-1]  # current value
    return np.sum(window < x) / (len(window) - 1) if len(window) > 1 else np.nan
    
class technicals:
    def __init__(self,ticker):
        self.df = pd.DataFrame()
        self.df['Close'] = yf.download(ticker)['Close']
        self.df['ret'] = self.df['Close'].pct_change()
        self.data = self.df.copy(deep=True)
        
    def calculate_macd(self,fast=26,slow=12,length=9):
        df = self.df.copy(deep=True)
        df["Fast"] = df['Close'].ewm(span=fast).mean()
        df["Slow"] = df['Close'].ewm(span=slow).mean()
    
        df['MACD'] = df["Slow"]-df["Fast"]
        df['Signal'] = df['MACD'].ewm(span=length).mean()
    
        df['val'] = df['MACD']-df['Signal']
        
        return df[['MACD','Signal','val']]

    
    def relative_strength_index(self,period=14):
        df = self.df.copy(deep=True)
        df['ret'] = df['Close'].pct_change()
        gain = df['ret'].clip(lower=0)
        loss = -df['ret'].clip(upper=0)
        
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
    
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['rsi'] = rsi
        return df[['rsi']],rsi

    def bollinger_band(self,period=20):
        df = self.df.copy(deep=True)
        df['std'] = df['Close'].rolling(period).std()
        df['mean'] = df['Close'].rolling(period).mean()
        df['upper'] = df['mean']+2*df['std']
        df['lower'] = df['mean']-2*df['std']
        return df[['Close','mean','upper','lower']]

    def generate_macd_signal(self,threshold=0.7,window=60):
        df2 = self.calculate_macd(fast=26,slow=12,length=9)
        df2['Ret'] = self.df['ret']

        df2['pct_rank'] = (df2['val'].rolling(window=window,min_periods=window).apply(percent_rank, raw=True)-0.5)*2
        
        df3 = df2[['Ret','pct_rank']].dropna()
        # df3['pct_rank_adj'] = np.where(np.abs(df3['pct_rank'])>0.4,df3['pct_rank'],np.nan)
        df3['rank'] = df3['pct_rank'].shift(1)
        df3['signal'] = np.where(np.abs(df3['rank'])>threshold,df3['rank']*df3['Ret'],np.nan)
        signal_today = df3['pct_rank'].iloc[-1]

        return signal_today
        
