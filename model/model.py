# model.py

import uuid
from arango import ArangoClient
from collections import defaultdict

# Các hằng số
GRADE_ORDER = {
    "GM": 1,
    "RM": 2,
    "DM": 3,
    "FM": 4,
    "SF": 5,
    "FC": 5
}

VALID_GRADES = {"SF", "FC", "DM"}

# Model đại lý
class Agency:
    def __init__(self, name, region, manager):
        self.name = name
        self.region = region
        self.manager = manager
        self._key = str(uuid.uuid4())

    def to_dict(self):
        return {
            "_key": self._key,
            "name": self.name,
            "region": self.region,
            "manager": self.manager
        }

# Kết nối và thao tác CSDL
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

    def fetch_agents(self):
        return list(self.db.collection("dms_agent_direct_indirect").all())

    def fetch_agent_details(self, relations=None, only_common=False):
        if not self.db.has_collection("dms_agent_detail"):
            return {}

        detail_col = self.db.collection("dms_agent_detail")

        if not only_common or not relations:
            details = list(detail_col.all())
        else:
            related_codes = set()
            for rel in relations:
                if "agent_code" in rel:
                    related_codes.add(str(rel["agent_code"]))
                if "child_code" in rel:
                    related_codes.add(str(rel["child_code"]))

            codes_list = [str(code) for code in related_codes]

            query = """
            FOR doc IN dms_agent_detail
                FILTER TO_STRING(doc.agent_code) IN @codes
                RETURN doc
            """
            cursor = self.db.aql.execute(query, bind_vars={"codes": codes_list})
            details = list(cursor)

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
        return list(cursor)

    def fetch_commission_details(self, from_date, to_date, offset=0, limit=20, search=None):
        query = """
        LET fromDate = @from_date
        LET toDate = @to_date

        LET matched_agents = (
            FOR p IN dms_policy_for_premium
                FILTER p.applied_premium_date >= fromDate
                    AND p.applied_premium_date <= toDate
                COLLECT agent_code = p.servicing_agent INTO grouped
                RETURN DISTINCT agent_code
        )

        FOR a IN dms_agent_detail
            FILTER a.agent_code IN matched_agents
            {{search_filter}}
            LET policies = (
                FOR p IN dms_policy_for_premium
                    FILTER p.servicing_agent == a.agent_code
                        AND p.applied_premium_date >= fromDate
                        AND p.applied_premium_date <= toDate
                    RETURN {
                        policy_no: p.policy_no,
                        policy_status: p.policy_status,
                        issued_date: p.issued_date,
                        applied_premium_date: p.applied_premium_date,
                        ack_date: p.ack_date,
                        freelook: p.freelook,
                        policy_type: p.policy_type,
                        policy_remark: p.policy_remark,
                        fyp: p.fyp,
                        fyc: p.fyc
                    }
            )
            LIMIT @offset, @limit
            RETURN {
                agent_code: a.agent_code,
                agent_name: a.agent_name,
                grade: a.grade,
                agent_status: a.agent_status,
                date_appointed: a.date_appointed,
                policies: policies
            }
        """

        bind_vars = {
            "from_date": from_date,
            "to_date": to_date,
            "offset": offset,
            "limit": limit
        }

        if search:
            search_filter = "AND (CONTAINS(LOWER(a.agent_code), LOWER(@search)) OR CONTAINS(LOWER(a.agent_name), LOWER(@search)) OR CONTAINS(LOWER(a.policies.policy_no), LOWER(@search)))"
            bind_vars["search"] = search
            
        else:
            search_filter = ""

        final_query = query.replace("{{search_filter}}", search_filter)
    
        cursor = self.db.aql.execute(final_query, bind_vars=bind_vars)
        return list(cursor)

    def count_commission_details(self, from_date, to_date, search=None):
        query = """
        RETURN LENGTH(
            FOR p IN dms_policy_for_premium
                FILTER p.applied_premium_date >= @from_date
                    AND p.applied_premium_date <= @to_date
                RETURN 1
        )
        """
        cursor = self.db.aql.execute(query, bind_vars={
            "from_date": from_date,
            "to_date": to_date
        })
        return next(cursor, 0)

    def fetch_commission_summary(self, from_date, to_date, offset=0, limit=20, search=None):
        query = """
        LET fromDate = @from_date
        LET toDate = @to_date
        LET typeCode = "COM"

        FOR doc IN Calculate_For_Agent
            FILTER doc.type_code == typeCode
                AND doc.calculated_from == fromDate
                AND doc.calculated_to == toDate
                {search_filter}
            SORT doc.agent_code
            LIMIT @offset, @limit
            RETURN doc
        """

        search_filter = ""
        bind_vars = {
            "from_date": from_date,
            "to_date": to_date,
            "offset": offset,
            "limit": limit,
        }

        if search:
            search_filter = "AND (CONTAINS(LOWER(doc.agent_code), LOWER(@search)) OR CONTAINS(LOWER(doc.agent_name), LOWER(@search)))"
            bind_vars["search"] = search

        final_query = query.replace("{search_filter}", search_filter)

        cursor = self.db.aql.execute(final_query, bind_vars=bind_vars)
        return list(cursor)


    def count_commission_summary(self, from_date, to_date, search=None):
        query = """
        RETURN LENGTH(
            FOR doc IN Calculate_For_Agent
                FILTER doc.type_code == "COM"
                    AND doc.calculated_from == @from_date
                    AND doc.calculated_to == @to_date
                    {search_filter}
                RETURN 1
        )
        """
        search_filter = ""
        bind_vars = {
            "from_date": from_date,
            "to_date": to_date
        }

        if search:
            search_filter = "AND (CONTAINS(LOWER(doc.agent_code), LOWER(@search)) OR CONTAINS(LOWER(doc.agent_name), LOWER(@search)))"
            bind_vars["search"] = search

        final_query = query.replace("{search_filter}", search_filter)
        cursor = self.db.aql.execute(final_query, bind_vars=bind_vars)
        return next(cursor, 0)

        if search_term:
            filter_clause = """
            AND (LIKE(LOWER(doc.agent_code), LOWER(@search_term), true)
                OR LIKE(LOWER(doc.agent_name), LOWER(@search_term), true))
            """
            bind_vars["search_term"] = f"%{search_term}%"

        query = query.replace("{{filter_clause}}", filter_clause)
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    
    def fetch_monthly_summary(self, from_date, to_date, offset=0, limit=20, search=None):
        query = """
        LET fromDate = @from_date
        LET toDate = @to_date
        LET typeCode = "MONTHLY"

        FOR doc IN Calculate_For_Agent
            FILTER doc.type_code == typeCode
                AND doc.calculated_from == fromDate
                AND doc.calculated_to == toDate
                {search_filter}
            SORT doc.agent_code
            LIMIT @offset, @limit
            RETURN doc
        """

        search_filter = ""
        bind_vars = {
            "from_date": from_date,
            "to_date": to_date,
            "offset": offset,
            "limit": limit,
        }

        if search:
            search_filter = "AND (CONTAINS(LOWER(doc.agent_code), LOWER(@search)) OR CONTAINS(LOWER(doc.agent_name), LOWER(@search)))"
            bind_vars["search"] = search

        final_query = query.replace("{search_filter}", search_filter)

        cursor = self.db.aql.execute(final_query, bind_vars=bind_vars)
        return list(cursor)


    def count_monthly_summary(self, from_date, to_date, search=None):
        query = """
        RETURN LENGTH(
            FOR doc IN Calculate_For_Agent
                FILTER doc.type_code == "MONTHLY"
                    AND doc.calculated_from == @from_date
                    AND doc.calculated_to == @to_date
                    {search_filter}
                RETURN 1
        )
        """
        search_filter = ""
        bind_vars = {
            "from_date": from_date,
            "to_date": to_date
        }

        if search:
            search_filter = "AND (CONTAINS(LOWER(doc.agent_code), LOWER(@search)) OR CONTAINS(LOWER(doc.agent_name), LOWER(@search)))"
            bind_vars["search"] = search

        final_query = query.replace("{search_filter}", search_filter)
        cursor = self.db.aql.execute(final_query, bind_vars=bind_vars)
        return next(cursor, 0)


        if search_term:
            filter_clause = """
            AND (LIKE(LOWER(doc.agent_code), LOWER(@search_term), true)
                OR LIKE(LOWER(doc.agent_name), LOWER(@search_term), true))
            """
            bind_vars["search_term"] = f"%{search_term}%"

        query = query.replace("{{filter_clause}}", filter_clause)
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)


# Hàm phụ trợ sắp xếp theo cấp bậc
def sort_nodes_by_grade(nodes):
    stack = list(nodes)
    while stack:
        node = stack.pop()
        if "children" in node:
            node["children"].sort(key=lambda x: GRADE_ORDER.get(x["grade"], 99))
            stack.extend(node["children"])
