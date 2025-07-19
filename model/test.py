
from arango import ArangoClient



client = ArangoClient(hosts='14.169.199.248:8529')

db = client.db(
    'DMS',
    username='khoatmt',
    password='123456'
)

server_info = db.version()
print("Connected to ArangoDB:", server_info)