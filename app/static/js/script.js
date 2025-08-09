class PortfolioManager {
    constructor() {
        this.portfolio = new Map();
        this.chart = null;
        this.totalValue = 0;
        this.portfolioDayReturnValue = 0;
        this.benchmarkDayReturn = 0;
        this.benchmarkDayReturnValue = 0;
        this.var99Percent = 0;  // Changed from var95Percent
        this.var99Value = 0;    // Changed from var95Value
        this.currencyFormatter = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        this.initializeChart();
        this.bindEvents();
        this.loadExistingPortfolio();
    }

    async loadExistingPortfolio() {
        try {
            const response = await fetch('/api/portfolio');
            if (response.ok) {
                const data = await response.json();
                console.log('Portfolio data loaded:', data);
                
                // Store return values from API response
                this.portfolioDayReturnValue = data.day_return_value || 0;
                this.benchmarkDayReturn = data.benchmark_day_return || 0;
                this.benchmarkDayReturnValue = data.benchmark_day_return_value || 0;
                this.var99Percent = data.var_99_percent || 0;  // Changed from var_95_percent
                this.var99Value = data.var_99_value || 0;      // Changed from var_95_value
                
                // Load portfolio data
                if (data.data && data.data.length > 0) {
                    this.portfolio = new Map(
                        data.data.map(stock => [stock.symbol, stock])
                    );
                    this.updateDisplay();
                }
                
                // Update return displays
                this.updateDayReturnValues();
                this.updateVarDisplay();
            }
        } catch (error) {
            console.error('Error loading portfolio:', error);
        }
    }

    async refreshPortfolioData() {
        try {
            const response = await fetch('/api/portfolio');
            if (response.ok) {
                const data = await response.json();
                console.log('Refreshed portfolio data:', data);
                
                // Update return values
                this.portfolioDayReturnValue = data.day_return_value || 0;
                this.benchmarkDayReturn = data.benchmark_day_return || 0;
                this.benchmarkDayReturnValue = data.benchmark_day_return_value || 0;
                this.var99Percent = data.var_99_percent || 0;  // Changed from var_95_percent
                this.var99Value = data.var_99_value || 0;      // Changed from var_95_value
                
                // Update return displays
                this.updateDayReturnValues();
                this.updateVarDisplay();
            }
        } catch (error) {
            console.error('Error refreshing portfolio data:', error);
        }
    }

    initializeChart() {
        const ctx = document.getElementById('compositionChart').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', 
                        '#4BC0C0', '#9966FF', '#FF9F40'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    bindEvents() {
        document.getElementById('stockForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleStockSubmit();
        });

        // Add event delegation for delete buttons
        document.getElementById('holdingsTable').addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-stock')) {
                const symbol = e.target.dataset.symbol;
                this.deleteStock(symbol);
            }
        });

        // Update export button handler
        document.getElementById('savePortfolio').addEventListener('click', async () => {
            try {
                // Configure save dialog options
                const options = {
                    suggestedName: `portfolio_${new Date().toISOString().slice(0,10)}.xlsx`,
                    types: [{
                        description: 'Excel Files',
                        accept: {
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
                        }
                    }]
                };

                // Show save dialog
                const handle = await window.showSaveFilePicker(options);
                
                // Get portfolio data
                const response = await fetch('/api/portfolio/download', {
                    headers: {
                        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Failed to generate portfolio file');
                }

                // Get the file data and write to selected location
                const blob = await response.blob();
                const writable = await handle.createWritable();
                await writable.write(blob);
                await writable.close();

                alert('Portfolio saved successfully!');

            } catch (error) {
                if (error.name === 'AbortError') {
                    // User cancelled the save dialog
                    return;
                }
                console.error('Export error:', error);
                alert(`Failed to export portfolio: ${error.message}`);
            }
        });

        // Add load portfolio handler
        document.getElementById('loadPortfolio').addEventListener('click', () => {
            document.getElementById('portfolioFile').click();
        });

        document.getElementById('portfolioFile').addEventListener('change', async (event) => {
            try {
                const file = event.target.files[0];
                if (!file) return;

                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/portfolio/load', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to load portfolio');
                }

                const result = await response.json();
                
                // Update portfolio display
                this.portfolio = new Map(
                    result.data.map(stock => [stock.symbol, stock])
                );
                this.updateDisplay();
                
                alert('Portfolio loaded successfully!');
                
            } catch (error) {
                console.error('Load error:', error);
                alert(`Failed to load portfolio: ${error.message}`);
            } finally {
                // Reset file input
                event.target.value = '';
            }
        });
    }

    async handleStockSubmit() {
        const symbolInput = document.getElementById('tickerSymbol');
        const quantityInput = document.getElementById('quantity');
        
        const symbol = symbolInput.value.toUpperCase();
        const quantity = parseInt(quantityInput.value);

        if (!symbol || !quantity) {
            alert('Please enter both symbol and quantity');
            return;
        }

        try {
            await this.addStock(symbol, quantity);
            // Clear form inputs after successful addition
            symbolInput.value = '';
            quantityInput.value = '';
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }

    async addStock(symbol, quantity) {
        try {
            const stockData = await this.fetchStockData(symbol, quantity);
            // Store the returns with the stock data
            this.portfolio.set(symbol, {
                ...stockData,
                value: stockData.price * stockData.quantity
            });
            this.updateDisplay();
            // Refresh portfolio data to get updated return values
            await this.refreshPortfolioData();
        } catch (error) {
            throw new Error(`Failed to add ${symbol}: ${error.message}`);
        }
    }

    async deleteStock(symbol) {
        try {
            const response = await fetch(`/api/portfolio/${symbol}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Failed to delete stock');
            await this.updatePortfolio();
        } catch (error) {
            throw new Error(`Failed to delete ${symbol}: ${error.message}`);
        }
    }

    async updatePortfolio() {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        
        this.portfolio = new Map(
            data.data.map(stock => [stock.symbol, stock])
        );
        
        // Store additional return data
        this.portfolioDayReturnValue = data.day_return_value || 0;
        this.benchmarkDayReturn = data.benchmark_day_return || 0;
        this.benchmarkDayReturnValue = data.benchmark_day_return_value || 0;
        this.var99Percent = data.var_99_percent || 0;  // Changed from var_95_percent
        this.var99Value = data.var_99_value || 0;      // Changed from var_95_value
        
        this.updateDisplay();
    }

    updateTotalValue() {
        this.totalValue = Array.from(this.portfolio.values())
            .reduce((sum, stock) => sum + stock.value, 0);
    }

    updateDisplay() {
        this.updateTable(); // Fixed: was this.updateHoldingsTable()
        this.updatePortfolioValue();
        this.updateChart();
        this.updateVarDisplay();
        this.updateDayReturnValues(); // Added this call
    }

    createTableRow(symbol, data) {
        const row = document.createElement('tr');
        const totalValue = this.getTotalValue(); // Use method instead of class property
        const percentage = totalValue > 0 ? ((data.value / totalValue) * 100).toFixed(2) : '0.00';
        
        row.innerHTML = `
            <td>${symbol} <small class="text-muted">${data.name || ''}</small></td>
            <td>${data.quantity}</td>
            <td>${this.currencyFormatter.format(data.price)}</td>
            <td>${this.currencyFormatter.format(data.value)}</td>
            <td>${percentage}%</td>
            <td>
                <button class="btn btn-danger btn-sm delete-stock" 
                        data-symbol="${symbol}">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        `;
        return row;
    }

    updateTable() { // This method exists and is correct
        const tbody = document.getElementById('holdingsTable');
        tbody.innerHTML = '';

        for (const [symbol, data] of this.portfolio) {
            tbody.appendChild(this.createTableRow(symbol, data));
        }
    }

    updateChart() {
        const labels = Array.from(this.portfolio.keys());
        const values = Array.from(this.portfolio.values())
            .map(stock => stock.value);

        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = values;
        this.chart.update();
    }

    getTotalValue() {
        return Array.from(this.portfolio.values())
            .reduce((sum, stock) => sum + stock.value, 0);
    }

    updatePortfolioValue() {
        const totalValue = this.getTotalValue();
        document.getElementById('portfolioValue').textContent = 
            this.currencyFormatter.format(totalValue);
        
        // Get returns directly from portfolio data
        const dayReturn = this.calculateDayReturn();
        const yearReturn = this.calculateYearReturn();
        
        console.log('Day Return:', dayReturn); // Debug log
        console.log('Year Return:', yearReturn); // Debug log
        
        this.updateReturnDisplay('dayReturn', 'dayReturnIcon', dayReturn);
        this.updateReturnDisplay('yearReturn', 'yearReturnIcon', yearReturn);
        
        // Update day return value displays
        this.updateDayReturnValues();
    }

    updateDayReturnValues() {
        console.log('Updating day return values:', {
            portfolioDayReturnValue: this.portfolioDayReturnValue,
            benchmarkDayReturn: this.benchmarkDayReturn,
            benchmarkDayReturnValue: this.benchmarkDayReturnValue
        });

        // Update portfolio day return value
        const portfolioValueElement = document.getElementById('portfolioDayReturnValue');
        if (portfolioValueElement) {
            const colorClass = this.portfolioDayReturnValue >= 0 ? 'text-success' : 'text-danger';
            const sign = this.portfolioDayReturnValue >= 0 ? '+' : '';
            portfolioValueElement.innerHTML = `<span class="${colorClass}">${sign}${this.currencyFormatter.format(Math.abs(this.portfolioDayReturnValue))}</span>`;
        }
        
        // Update benchmark day return value
        const benchmarkValueElement = document.getElementById('benchmarkDayReturnValue');
        if (benchmarkValueElement) {
            const colorClass = this.benchmarkDayReturnValue >= 0 ? 'text-success' : 'text-danger';
            const sign = this.benchmarkDayReturnValue >= 0 ? '+' : '';
            const benchmarkSign = this.benchmarkDayReturn >= 0 ? '+' : '';
            benchmarkValueElement.innerHTML = `
                <span class="${colorClass}">
                    ${sign}${this.currencyFormatter.format(Math.abs(this.benchmarkDayReturnValue))} 
                    (NIFTY: ${benchmarkSign}${Math.abs(this.benchmarkDayReturn).toFixed(2)}%)
                </span>
            `;
        }
    }

    updateVarDisplay() {
        console.log('Updating VaR display:', {
            var99Percent: this.var99Percent,  // Changed from var95Percent
            var99Value: this.var99Value       // Changed from var95Value
        });

        // Update VaR display
        const varElement = document.getElementById('portfolioVaR');
        if (varElement) {
            const varPercentFormatted = Math.abs(this.var99Percent).toFixed(2);  // Changed from var95Percent
            const varValueFormatted = this.currencyFormatter.format(Math.abs(this.var99Value));  // Changed from var95Value
            
            varElement.innerHTML = `
                <h6 class="mb-0 text-danger">${varPercentFormatted}%</h6>
                <small class="text-muted">VaR (99%)</small>
                <div class="return-value">
                    <small class="text-danger">${varValueFormatted}</small>
                </div>
            `;
        }
    }

    updateReturnDisplay(elementId, iconId, returnValue) {
        const element = document.getElementById(elementId);
        const iconElement = document.getElementById(iconId);
        
        if (!element || !iconElement) {
            console.warn(`Element not found: ${elementId} or ${iconId}`);
            return;
        }
        
        // Ensure return value is a number
        const numericReturn = parseFloat(returnValue) || 0;
        
        // Format the return value
        element.textContent = `${numericReturn.toFixed(2)}%`;
        
        // Update icon and color
        const icon = numericReturn >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
        const colorClass = numericReturn >= 0 ? 'text-success' : 'text-danger';
        
        iconElement.innerHTML = `<i class="fas ${icon} ${colorClass}"></i>`;
        element.className = `mb-0 ${colorClass}`;
    }

    calculateDayReturn() {
        let weightedReturn = 0;
        let totalValue = this.getTotalValue();
        
        if (totalValue === 0) return 0;
        
        for (const [_, data] of this.portfolio) {
            const stockWeight = data.value / totalValue;
            weightedReturn += (data.dayReturn || 0) * stockWeight;
        }
        
        console.log('Portfolio data:', Array.from(this.portfolio.values())); // Debug log
        console.log('Weighted day return:', weightedReturn); // Debug log
        
        return weightedReturn;
    }

    calculateYearReturn() {
        let weightedReturn = 0;
        let totalValue = this.getTotalValue();
        
        if (totalValue === 0) return 0;
        
        for (const [_, data] of this.portfolio) {
            const stockWeight = data.value / totalValue;
            weightedReturn += (data.yearReturn || 0) * stockWeight;
        }
        
        console.log('Weighted year return:', weightedReturn); // Debug log
        
        return weightedReturn;
    }

    async fetchStockData(symbol, quantity) {
        try {
            const response = await fetch(`/api/stock/${symbol}?quantity=${quantity}`);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to fetch stock data');
            }
            return await response.json();
        } catch (error) {
            throw new Error(`Failed to fetch data for ${symbol}: ${error.message}`);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.portfolioManager = new PortfolioManager();
});
