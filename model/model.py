import uuid
from arango import ArangoClient
from collections import defaultdict, deque


GRADE_ORDER = {
    "GM": 1,
    "RM": 2,
    "DM": 3,
    "FM": 4,
    "SF": 5,
    "FC": 5
}

VALID_GRADES = {"SF", "FC", "DM"}


class Agency:
    def __init__(self, name, region, manager):
        self.name = name
        self.region = region
        self.manager = manager
        self._key = str(uuid.uuid4())  # Sinh khóa ngẫu nhiên

    def to_dict(self):
        return {
            "_key": self._key,
            "name": self.name,
            "region": self.region,
            "manager": self.manager
        }


class AgencyDatabase:
    def __init__(self, db_name="agency_db", collection_name="agencies"):
        client = ArangoClient()
        self.sys_db = client.db("_system", username="root", password="123456")

        if not self.sys_db.has_database(db_name):
            self.sys_db.create_database(db_name)

        self.db = client.db(db_name, username="root", password="123456")

        if not self.db.has_collection(collection_name):
            self.collection = self.db.create_collection(collection_name)
        else:
            self.collection = self.db.collection(collection_name)

    def fetch_agent_details(self, relations=None, only_common=False):
        if not self.db.has_collection("dms_agent_detail"):
            return {}

        detail_col = self.db.collection("dms_agent_detail")

        if not only_common or not relations:
            details = list(detail_col.all())
        else:
            # Lấy danh sách agent_code và child_code từ relations
            related_codes = set()
            for rel in relations:
                if "agent_code" in rel:
                    related_codes.add(str(rel["agent_code"]))
                if "child_code" in rel:
                    related_codes.add(str(rel["child_code"]))

            codes_list = list(related_codes)

            query = """
            FOR doc IN dms_agent_detail
                FILTER doc.agent_code IN @codes
                RETURN doc
            """
            cursor = self.db.aql.execute(query, bind_vars={"codes": codes_list})
            details = list(cursor)

        # Tạo detail_map và in dữ liệu thử
        detail_map = {}
        for detail in details:
            code = str(detail.get("agent_code"))
            detail_map[code] = detail

        return detail_map

    def bring_on_new_agency(self, name, region, manager):
        new_agency = Agency(name, region, manager)
        self.collection.insert(new_agency.to_dict())
        print(f"✅ Thêm đại lý '{name}' vào CSDL.")

    def show_me_all_the_agencies(self):
        agencies = list(self.collection.all())
        return [
            {
                "name": agency.get("name", ""),
                "region": agency.get("region", ""),
                "manager": agency.get("manager", "")
            }
            for agency in agencies
        ]

    def find_agencies_by_name(self, search_term):
        query = f"""
        FOR agency IN {self.collection.name}
            FILTER CONTAINS(LOWER(agency.name), LOWER(@search_term))
            RETURN agency
        """
        cursor = self.db.aql.execute(query, bind_vars={'search_term': search_term})
        results = list(cursor)

        if not results:
            print(f"❌ Không tìm thấy đại lý tên '{search_term}'")
        else:
            print(f"\n🔍 Kết quả tìm kiếm '{search_term}':")
            for agency in results:
                print(f"- {agency['name']} ({agency['region']}) - Quản lý: {agency['manager']}")

        return results

    def fetch_agents(self):
        cursor = self.db.collection("dms_agent_direct_indirect").all()
        return list(cursor)



def build_tree_from_relation_bfs(relations, detail_map=None):
    from collections import deque, defaultdict

    node_map = {}
    children_map = defaultdict(list)
    all_children = set()

    # Chuẩn hóa relations
    for rel in relations:
        a_code = str(rel.get("agent_code", "")).strip()
        c_code = str(rel.get("child_code", "")).strip()

        # Agent cha
        if a_code and a_code not in node_map and rel.get("agent_grade") in VALID_GRADES:
            node_map[a_code] = {
                "code": a_code,
                "name": rel.get("agent_name", ""),
                "grade": rel.get("agent_grade", ""),
                "status": rel.get("agent_status", ""),
                "parent_code": rel.get("agent_parent_code", ""),
                "raw": rel,
                "children": []
            }
            if detail_map:
                detail = detail_map.get(a_code)
                if detail:
                    node_map[a_code].update(detail)

        # Agent con
        if c_code and c_code not in node_map and rel.get("child_grade") in VALID_GRADES:
            node_map[c_code] = {
                "code": c_code,
                "name": rel.get("child_name", ""),
                "grade": rel.get("child_grade", ""),
                "status": rel.get("child_status", ""),
                "parent_code": rel.get("agent_code", ""),
                "raw": rel,
                "children": []
            }
            if detail_map:
                detail = detail_map.get(c_code)
                if detail:
                    node_map[c_code].update(detail)

        # Gán quan hệ cha - con
        if a_code and c_code:
            children_map[a_code].append(c_code)
            all_children.add(c_code)

    # Tìm node gốc
    root_nodes = [node_map[code] for code in node_map if code not in all_children]
    if not root_nodes:
        root_nodes = [{
            "code": "ROOT",
            "name": "ROOT",
            "grade": "",
            "children": list(node_map.values())
        }]

    # BFS traversal
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


def sort_nodes_by_grade(nodes):
    stack = list(nodes)
    while stack:
        node = stack.pop()
        if "children" in node:
            node["children"].sort(key=lambda x: GRADE_ORDER.get(x["grade"], 99))
            stack.extend(node["children"])
