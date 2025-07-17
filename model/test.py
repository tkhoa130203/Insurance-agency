
from arango import ArangoClient



client = ArangoClient(hosts='http://14.169.199.248:8529')

db = client.db(
    'DMS',
    username='khoatmt',
    password='123456'
)

# Kiểm tra kết nối và collection
if db.has_collection("agencies"):
    agencies_collection = db.collection("agent")
    
    # Thực hiện truy vấn AQL
query = """
FOR a IN agencies
LIMIT 5
RETURN a
"""

cursor = db.aql.execute(query)

# In kết quả
for doc in cursor:
    print(doc)
else:
    print("Collection 'agent' không tồn tại!")