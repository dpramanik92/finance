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
    Session(app)
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(stock_bp)
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5200))
    app.run(host='0.0.0.0', port=port, debug=True)