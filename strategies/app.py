from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Finance App"

if __name__ == '__main__':
    app.run(debug=True)