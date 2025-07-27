# controller.py

from collections import defaultdict, deque
from model.model import VALID_GRADES, sort_nodes_by_grade
from model.model import AgencyDatabase

def build_tree_from_relation_bfs(relations, detail_map=None):
    node_map = {}
    children_map = defaultdict(list)
    all_children = set()

    for rel in relations:
        a_code = str(rel.get("agent_code", "")).strip()
        c_code = str(rel.get("child_code", "")).strip()

        # Cha
        if a_code:
            if a_code not in node_map and rel.get("agent_grade") in VALID_GRADES:
                node_map[a_code] = {
                    "code": a_code,
                    "name": rel.get("agent_name", ""),
                    "grade": rel.get("agent_grade", ""),
                    "status": rel.get("agent_status", ""),
                    "parent_code": rel.get("agent_parent_code", ""),
                    "children": []
                }
                if detail_map and a_code in detail_map:
                    node_map[a_code].update(detail_map[a_code])

        # Con
        if c_code:
            if c_code not in node_map and rel.get("child_grade") in VALID_GRADES:
                node_map[c_code] = {
                    "code": c_code,
                    "name": rel.get("child_name", ""),
                    "grade": rel.get("child_grade", ""),
                    "status": rel.get("child_status", ""),
                    "parent_code": rel.get("agent_code", ""),
                    "children": []
                }
                if detail_map and c_code in detail_map:
                    node_map[c_code].update(detail_map[c_code])

        if a_code and c_code:
            children_map[a_code].append(c_code)
            all_children.add(c_code)

    root_nodes = [node_map[code] for code in node_map if code not in all_children]

    if not root_nodes:
        root_nodes = [{
            "code": "ROOT",
            "name": "ROOT",
            "grade": "",
            "children": list(node_map.values())
        }]

    queue = deque(root_nodes)
    while queue:
        current = queue.popleft()
        for child_code in children_map.get(current["code"], []):
            child_node = node_map.get(child_code)
            if child_node:
                current["children"].append(child_node)
                queue.append(child_node)

    sort_nodes_by_grade(root_nodes)
    return root_nodes
