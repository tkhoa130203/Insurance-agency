
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, render_template, request, redirect, url_for
from model.model import AgencyDatabase
from controller.controller import build_tree_from_relation_bfs, sort_nodes_by_grade, remove_duplicate_policies
from model.model import GRADE_ORDER, VALID_GRADES

# Jinja2 filter: combine 2 dicts (node, node.details)
def combine_dicts(a, b):
    if not isinstance(a, dict):
        a = dict(a)
    if not isinstance(b, dict):
        b = dict(b)
    merged = a.copy()
    merged.update(b)
    return merged


GRADE_ORDER = {
    "GM": 1,
    "RM": 2,
    "DM": 3,
    "FM": 4,
    "SF": 5,
    "FC": 5  # SF và FC là cùng cấp
}

app = Flask(__name__,  template_folder='view/templates', static_folder='view/static')
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
    search = request.args.get('search', '').strip().lower()
    
    # Lấy danh sách quan hệ đại lý và chi tiết
    agents = db.fetch_agents()
    detail_map = db.fetch_agent_details(agents, only_common=True)

    # Nếu có tìm kiếm, lọc chỉ các quan hệ có chứa từ khóa trong mã hoặc tên
    if search:
        filtered_codes = set()
        for rel in agents:
            if (
                search in str(rel.get("agent_name", "")).lower()
                or search in str(rel.get("child_name", "")).lower()
                or search in str(rel.get("agent_code", "")).lower()
                or search in str(rel.get("child_code", "")).lower()
            ):
                filtered_codes.add(rel.get("agent_code"))
                filtered_codes.add(rel.get("child_code"))

        agents = [
            rel for rel in agents
            if rel.get("agent_code") in filtered_codes or rel.get("child_code") in filtered_codes
        ]

    roots = []
    children_map = {}
    node_map = {}

    for rel in agents:
        code = rel.get("agent_code")
        child_code = rel.get("child_code")
        parent_code = rel.get("agent_parent_code")

        if code not in node_map:
            node_map[code] = {
                "code": code,
                "name": rel.get("agent_name", ""),
                "grade": rel.get("agent_grade", ""),
                "parent_code": parent_code,
                "children": []
            }
            if code in detail_map:
                node_map[code].update(detail_map[code])

        if child_code and child_code not in node_map:
            node_map[child_code] = {
                "code": child_code,
                "name": rel.get("child_name", ""),
                "grade": rel.get("child_grade", ""),
                "parent_code": code,
                "children": []
            }
            if child_code in detail_map:
                node_map[child_code].update(detail_map[child_code])

        if code and child_code:
            children_map.setdefault(code, [])
            if child_code not in children_map[code]:
                children_map[code].append(child_code)

    # Tìm root nodes theo cấp cao nhất (SF hoặc FC)
    max_level = max(GRADE_ORDER.values())
    for code, node in node_map.items():
        grade = node.get("grade")
        if grade and GRADE_ORDER.get(grade, 0) == max_level:
            roots.append(node)

    # Nếu có search: sắp xếp root node sao cho khớp nằm trên cùng
    if search:
        def score(node):
            name = node.get("name", "").lower()
            code = node.get("code", "").lower()
            return int(search in name or search in code)
        roots.sort(key=score, reverse=True)

    # Chỉ load 1 cấp con tiếp theo (SF/FC → FM...)
    from collections import deque
    queue = deque(roots)
    for _ in range(len(queue)):
        parent = queue.popleft()
        for child_code in children_map.get(parent["code"], []):
            child_node = node_map.get(child_code)
            if child_node:
                parent_grade = parent.get("grade", "")
                child_grade = child_node.get("grade", "")
                if GRADE_ORDER.get(child_grade, 0) < GRADE_ORDER.get(parent_grade, 0):
                    parent["children"].append(child_node)

    return render_template(
        'pages/sales_channel_structure.html',
        agent_tree=roots,
        detail_map=detail_map
    )


@app.route("/api/agent-children/<parent_code>")
def get_agent_children(parent_code):
    agents = db.fetch_agents()
    detail_map = db.fetch_agent_details(agents, only_common=True)

    # Tìm tất cả grade của parent_code (vì có thể parent_code xuất hiện nhiều lần)
    parent_grades = set()
    for rel in agents:
        if str(rel.get("agent_code")) == parent_code:
            pg = rel.get("agent_grade")
            if pg:
                parent_grades.add(pg)

    # Nếu không tìm được grade → trả rỗng
    if not parent_grades:
        return jsonify([])

    # Lấy max grade trong trường hợp có nhiều bản ghi
    parent_grade = max(parent_grades, key=lambda g: GRADE_ORDER.get(g, 0))
    parent_level = GRADE_ORDER.get(parent_grade, 0)

    children = []
    for rel in agents:
        if str(rel.get("agent_code")) != parent_code:
            continue

        c_code = rel.get("child_code")
        c_grade = rel.get("child_grade")
        if not c_code or not c_grade:
            continue

        child_level = GRADE_ORDER.get(c_grade, 0)

        # Chỉ nhận con có cấp thấp hơn (VD: SF → FM)
        if child_level >= parent_level:
            continue

        node = {
            "code": c_code,
            "name": rel.get("child_name", ""),
            "grade": c_grade,
            "status": rel.get("child_status", ""),
            "parent_code": parent_code,
            "children": False  # chưa load children
        }
        if c_code in detail_map:
            node.update(detail_map[c_code])

        children.append(node)

    return jsonify(children)

@app.route('/api/agent-detail/<agent_code>')
def get_agent_detail(agent_code):
    try:
        cursor = db.db.aql.execute("""
            FOR d IN dms_agent_detail
                FILTER d.agent_code == @code
                RETURN d
        """, bind_vars={"code": agent_code})
        doc = next(cursor, None)

        if not doc:
            return jsonify({"error": "Agent not found"}), 200  # trả 200 để frontend không lỗi
        return jsonify(doc)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/commission')
def commission_page():
    tab = request.args.get('tab', 'summary')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    from_date = request.args.get('from', '2025-04-01')
    to_date = request.args.get('to', '2025-04-30')
    search = request.args.get('search', '').strip()

    if tab == 'summary':
        data = db.fetch_commission_summary(from_date, to_date, offset=offset, limit=per_page, search=search)
        total = db.count_commission_summary(from_date, to_date, search=search)
        return render_template(
            "pages/commission_summary.html",
            data=data,
            current_page=page,
            total_pages=(total + per_page - 1) // per_page,
            active_tab='summary',
            search=search
        )
    else:
        data = db.fetch_commission_details(from_date, to_date, offset=offset, limit=per_page, search=search)
        total = db.count_commission_details(from_date, to_date, search=search)
        return render_template(
            "pages/commission_detail.html",
            data=data,
            current_page=page,
            total_pages=(total + per_page - 1) // per_page,
            active_tab='detail',
            search=search
        )



@app.route('/export')
def export():
    return render_template('pages/export.html')


if __name__ == '__main__':
    app.run(debug=True, port=5050)

