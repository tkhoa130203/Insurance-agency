from arango import ArangoClient
from collections import defaultdict

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

    def __str__(self):
        return f"{self.name} ({self.region}) - Managed by {self.manager}"

    def to_dict(self):
        return {
            "name": self.name,
            "region": self.region,
            "manager": self.manager
        }


class AgencyDatabase:
    def fetch_agent_details(self):
        # Lấy toàn bộ chi tiết agent từ collection dms_agent_detail, trả về dict agent_code -> detail
        if not self.db.has_collection("dms_agent_detail"):
            return {}
        detail_col = self.db.collection("dms_agent_detail")
        details = list(detail_col.all())
        detail_map = {}
        for detail in details:
            code = detail.get("agent_code")
            if code:
                detail_map[code] = detail
        return detail_map
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


def build_tree_from_relation(relations, detail_map=None):
    node_map = {}
    children_map = defaultdict(list)
    all_children = set()

    if detail_map is None:
        detail_map = {}

    filtered = [
        rel for rel in relations
        if rel.get("agent_grade") in VALID_GRADES or rel.get("child_grade") in VALID_GRADES
    ]

    for rel in filtered:
        a_code = rel.get("agent_code")
        c_code = rel.get("child_code")

        # ----- Đại lý cha -----
        if a_code and a_code not in node_map and rel.get("agent_grade") in VALID_GRADES:
            merged = {}
            # Gộp tất cả field từ record direct_indirect
            merged.update(rel)
            # Gộp thêm từ detail nếu có
            if a_code in detail_map:
                merged.update(detail_map[a_code])
            # Chuẩn hóa tên và thông tin chính
            merged["code"] = a_code
            merged["name"] = rel.get("agent_name", "")
            merged["grade"] = rel.get("agent_grade", "")
            merged["children"] = []
            node_map[a_code] = merged

        # ----- Đại lý con -----
        if c_code and c_code not in node_map and rel.get("child_grade") in VALID_GRADES:
            merged = {}
            merged.update(rel)
            if c_code in detail_map:
                merged.update(detail_map[c_code])
            merged["code"] = c_code
            merged["name"] = rel.get("child_name", "")
            merged["grade"] = rel.get("child_grade", "")
            merged["children"] = []
            node_map[c_code] = merged

        # Gán quan hệ cha-con
        if a_code in node_map and c_code in node_map:
            children_map[a_code].append(c_code)
            all_children.add(c_code)

    # Gán children vào parent
    for parent_code, child_codes in children_map.items():
        node_map[parent_code]["children"] = [node_map[c] for c in child_codes]

    # Root
    root_nodes = [node for code, node in node_map.items() if code not in all_children]

    if not root_nodes:
        root_nodes = [{
            "code": "ROOT",
            "name": "ROOT",
            "grade": "",
            "children": list(node_map.values())
        }]

    sort_nodes_by_grade(root_nodes)
    return root_nodes


def sort_nodes_by_grade(nodes):
    stack = list(nodes)
    while stack:
        node = stack.pop()
        if "children" in node:
            node["children"].sort(key=lambda x: GRADE_ORDER.get(x["grade"], 99))
            stack.extend(node["children"])