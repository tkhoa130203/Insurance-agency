
# Jinja2 filter: combine 2 dicts (node, node.details)
def combine_dicts(a, b):
    if not isinstance(a, dict):
        a = dict(a)
    if not isinstance(b, dict):
        b = dict(b)
    merged = a.copy()
    merged.update(b)
    return merged

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for
from model.model import AgencyDatabase, build_tree_from_relation

app = Flask(__name__)
app.jinja_env.filters['combine'] = combine_dicts
db = AgencyDatabase()

@app.route('/')
def index():
    agencies = db.show_me_all_the_agencies()
    return render_template('pages/index.html', agencies=agencies)

@app.route('/add', methods=['GET', 'POST'])
def add_agency():
    if request.method == 'POST':
        name = request.form['name']
        region = request.form['region']
        manager = request.form['manager']
        db.bring_on_new_agency(name, region, manager)
        return redirect(url_for('index'))
    return render_template('pages/add.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        results = db.find_agencies_by_name(keyword)
    return render_template('search.html', results=results)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/share')
def share():
    return render_template('share.html')

@app.route('/change_password')
def change_password():
    return render_template('change_password.html')

@app.route('/logout')
def logout():
    # Add your logout logic here
    return redirect(url_for('index'))

@app.route('/agencies')
def list_agencies():
    agencies = db.show_me_all_the_agencies()
    return render_template('pages/list_agencies.html', agencies=agencies)

@app.route('/add_agency')
def add_agency_page():
    return render_template('pages/add_agency.html')

@app.route('/sales')
def sales():
    return render_template('pages/sales.html')

@app.route('/users')
def list_users():
    return render_template('pages/list_users.html')

@app.route('/roles')
def roles():
    return render_template('pages/roles.html')

@app.route('/add_user')
def add_user():
    return render_template('pages/add_user.html')

@app.route('/products')
def list_products():
    return render_template('pages/list_products.html')

@app.route('/add_product')
def add_product():
    return render_template('pages/add_product.html')

@app.route('/update_product')
def update_product():
    return render_template('pages/update_product.html')

@app.route('/contracts')
def list_contracts():
    return render_template('pages/list_contracts.html')

@app.route('/add_contract')
def add_contract():
    return render_template('pages/add_contract.html')

@app.route('/sales_channel_structure')
def sales_channel_structure():
    agents = db.fetch_agents()
    detail_map = db.fetch_agent_details()
    agent_tree = build_tree_from_relation(agents)
    return render_template('pages/sales_channel_structure.html', agent_tree=agent_tree, detail_map=detail_map)

@app.route('/export')
def export():
    return render_template('pages/export.html')

if __name__ == '__main__':
    app.run(debug=True, port=5050)

