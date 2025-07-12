import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for
from model.model import AgencyDatabase

app = Flask(__name__)
db = AgencyDatabase()

@app.route('/')
def index():
    agencies = db.show_me_all_the_agencies()
    return render_template('index.html', agencies=agencies)

@app.route('/add', methods=['GET', 'POST'])
def add_agency():
    if request.method == 'POST':
        name = request.form['name']
        region = request.form['region']
        manager = request.form['manager']
        db.bring_on_new_agency(name, region, manager)
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        results = db.find_agencies_by_name(keyword)
    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, port=5050)

