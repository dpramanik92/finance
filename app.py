from flask import Flask, session
from flask_session import Session
import os
from app.routes.main_routes import main
from app.routes.stock_routes import stock_bp
from datetime import timedelta

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    # Configure session
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_123')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
    
    # Ensure session directory exists
    session_dir = os.path.join(os.getcwd(), 'flask_session')
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    Session(app)
    
    # Add custom filters for Indian number formatting
    @app.template_filter('indian_currency')
    def indian_currency_filter(value):
        """Format number as Indian currency"""
        try:
            num = float(value)
            if num >= 10000000:  # 1 crore
                return f"₹{num/10000000:.2f} Cr"
            elif num >= 100000:  # 1 lakh
                return f"₹{num/100000:.2f} L"
            else:
                return f"₹{num:,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"
    
    @app.template_filter('indian_number')
    def indian_number_filter(value):
        """Format number in Indian style"""
        try:
            num = int(value)
            if num >= 10000000:  # 1 crore
                return f"{num/10000000:.1f} Cr"
            elif num >= 100000:  # 1 lakh
                return f"{num/100000:.1f} L"
            else:
                return f"{num:,}"
        except (ValueError, TypeError):
            return "0"
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(stock_bp)
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5200))
    app.run(host='0.0.0.0', port=port, debug=True)