from flask import render_template
from larva_library import app

@app.route('/')
def index():
    return render_template('index.html')