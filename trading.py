class Trading:
    def __init__(self,strategy,ticker,current_portfolio,threshold):
        self.strat = strategy(ticker)
        self.current = current_portfolio
        self.threshold = threshold
        self.stock = self.strat.df

    def generate_signal(self,indicator):
        if indicator == 'MACD':
            self.signal = self.strat.generate_macd_signal(threshold=self.threshold)
            return self.signal

    def execute_trade(self,indicator):
        self.generate_signal(indicator)
        equity = self.signal*self.value
        cash = (1-self.signal)*self.value
        self.equity = equity
        self.cash = cash
        self.value = equity+cash

        return equity,cash

    def calculate_return(self):
        self.equity = self.current['Equity'].iloc[-1]*(1+self.stock['Close'].pct_change().iloc[-1])
        self.value = self.equity+self.current['Cash'].iloc[-1]
        display(self.equity,self.value,self.stock['Close'].pct_change().iloc[1])
        
    def update_portfolio(self):
        self.current = pd.concat([self.current,pd.DataFrame({'Date':[datetime.datetime.today().date()],'Equity':[self.equity],'Cash':[self.cash],'Total':[self.value]}) ]) 
        self.current.drop_duplicates(inplace=True)