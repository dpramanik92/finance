document.addEventListener('DOMContentLoaded', function() {
    // Portfolio data structure
    let portfolio = {
        holdings: {},
        totalValue: 0,
        composition: {}
    };

    // Mock stock prices (in a real app, this would come from an API)
    const stockPrices = {
        'AAPL': 175.50,
        'GOOGL': 125.30,
        'MSFT': 330.20,
        'TSLA': 250.75,
        'AMZN': 140.60,
        'NVDA': 420.10
    };

    // Add to portfolio form handler
    const addToPortfolioForm = document.getElementById('addToPortfolioForm');
    if (addToPortfolioForm) {
        addToPortfolioForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const stockSymbol = document.getElementById('stockSymbol').value.toUpperCase();
            const quantity = parseInt(document.getElementById('quantity').value);
            
            if (!stockSymbol || !quantity || quantity <= 0) {
                alert('Please enter a valid stock symbol and quantity.');
                return;
            }
            
            // Check if stock price exists (mock validation)
            if (!stockPrices[stockSymbol]) {
                alert('Stock symbol not found. Please enter a valid symbol.');
                return;
            }
            
            addStockToPortfolio(stockSymbol, quantity);
            updatePortfolioDisplay();
            
            // Clear form
            addToPortfolioForm.reset();
        });
    }

    function addStockToPortfolio(symbol, quantity) {
        const price = stockPrices[symbol];
        const value = price * quantity;
        
        // Add or update holdings
        if (portfolio.holdings[symbol]) {
            portfolio.holdings[symbol].quantity += quantity;
            portfolio.holdings[symbol].value = portfolio.holdings[symbol].quantity * price;
        } else {
            portfolio.holdings[symbol] = {
                quantity: quantity,
                price: price,
                value: value
            };
        }
        
        // Update total portfolio value
        portfolio.totalValue = Object.values(portfolio.holdings)
            .reduce((total, holding) => total + holding.value, 0);
        
        // Update portfolio composition (percentages)
        updatePortfolioComposition();
    }

    function updatePortfolioComposition() {
        portfolio.composition = {};
        for (const [symbol, holding] of Object.entries(portfolio.holdings)) {
            portfolio.composition[symbol] = ((holding.value / portfolio.totalValue) * 100).toFixed(2);
        }
    }

    function updatePortfolioDisplay() {
        updatePortfolioValue();
        updateHoldingsTable();
        updateCompositionChart();
    }

    function updatePortfolioValue() {
        const portfolioValueElement = document.getElementById('portfolioValue');
        if (portfolioValueElement) {
            portfolioValueElement.textContent = `$${portfolio.totalValue.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
        }
    }

    function updateHoldingsTable() {
        const holdingsTableBody = document.getElementById('holdingsTableBody');
        if (!holdingsTableBody) return;
        
        holdingsTableBody.innerHTML = '';
        
        for (const [symbol, holding] of Object.entries(portfolio.holdings)) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${symbol}</td>
                <td>${holding.quantity}</td>
                <td>$${holding.price.toFixed(2)}</td>
                <td>$${holding.value.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })}</td>
                <td>${portfolio.composition[symbol]}%</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="removeStock('${symbol}')">
                        Remove
                    </button>
                </td>
            `;
            holdingsTableBody.appendChild(row);
        }
    }

    function updateCompositionChart() {
        const compositionContainer = document.getElementById('compositionChart');
        if (!compositionContainer) return;
        
        compositionContainer.innerHTML = '';
        
        for (const [symbol, percentage] of Object.entries(portfolio.composition)) {
            const barContainer = document.createElement('div');
            barContainer.className = 'composition-bar-container mb-2';
            
            barContainer.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold">${symbol}</span>
                    <span>${percentage}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${percentage}%" 
                         aria-valuenow="${percentage}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
            `;
            
            compositionContainer.appendChild(barContainer);
        }
    }

    // Global function to remove stock (accessible from HTML)
    window.removeStock = function(symbol) {
        if (confirm(`Are you sure you want to remove ${symbol} from your portfolio?`)) {
            delete portfolio.holdings[symbol];
            
            // Recalculate total value
            portfolio.totalValue = Object.values(portfolio.holdings)
                .reduce((total, holding) => total + holding.value, 0);
            
            // Update composition
            updatePortfolioComposition();
            
            // Update display
            updatePortfolioDisplay();
        }
    };

    // Initialize display
    updatePortfolioDisplay();
});