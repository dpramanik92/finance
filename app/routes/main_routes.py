from flask import Blueprint, render_template

main = Blueprint('main', __name__, template_folder='../templates')

from flask import Blueprint, render_template

# Create blueprint for main routes
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@main.route('/strategies')
def strategies():
    return render_template('strategies.html')

@main.route('/analysis')
def analysis():
    return render_template('analysis.html')

@main.route('/settings')
def settings():
    return render_template('settings.html')

@main.route('/about')
def about():
    return render_template('about.html')
