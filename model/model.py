"""
Module quản lý dữ liệu đại lý bảo hiểm, kết nối với ArangoDB.
"""

from arango import ArangoClient

class Agency:
    def __init__(self, name, region, manager):
        # Lưu thông tin đại lý
        self.name = name
        self.region = region
        self.manager = manager

    def __str__(self):
        return f"{self.name} ({self.region}) - Managed by {self.manager}"

    def to_dict(self):
        # Chuyển đổi  thành dict để lưu vào db
        return {
            "name": self.name,
            "region": self.region,
            "manager": self.manager
        }

class AgencyDatabase:
    """
    Quản lý thao tác với ArangoDB: thêm, truy vấn, hiển thị danh sách đại lý.
    """

    def __init__(self, db_name="agency_db", collection_name="agencies"):
        # Connect database
        client = ArangoClient()
        self.sys_db = client.db("_system", username="root", password="123456")
        # Nếu database chưa tồn tại thì tạo mới
        if not self.sys_db.has_database(db_name):
            self.sys_db.create_database(db_name)
        # Connect database chính
        self.db = client.db(db_name, username="root", password="123456")
        # Nếu collection chưa tồn tại thì tạo mới
        if not self.db.has_collection(collection_name):
            self.collection = self.db.create_collection(collection_name)
        else:
            self.collection = self.db.collection(collection_name)

    def bring_on_new_agency(self, name, region, manager):
        # Tạo Agency mới
        new_agency = Agency(name, region, manager)
        self.collection.insert(new_agency.to_dict())
        print(f"✅ Thêm đại lý '{name}' vào CSDL.")

    def show_me_all_the_agencies(self):
        # List all đại lý trong collection, trả về list dict cho Flask
        agencies = list(self.collection.all())
        result = []
        for agency in agencies:
            result.append({
                "name": agency.get("name", ""),
                "region": agency.get("region", ""),
                "manager": agency.get("manager", "")
            })
        return result

    def find_agencies_by_name(self, search_term):
        # Tìm kiếm đại lý theo tên
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
