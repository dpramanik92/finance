from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import routes
    from app.routes.main_routes import main_bp
    from app.routes.api_routes import api_bp

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)