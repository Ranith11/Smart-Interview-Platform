import sqlite3
import chromadb
from chromadb.api.configuration import CollectionConfigurationInternal

db_path = "chroma_db/chroma.sqlite3"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

valid_json = CollectionConfigurationInternal().to_json_str()
cur.execute("UPDATE collections SET config_json_str = ? WHERE config_json_str = '{}'", (valid_json,))
conn.commit()
print("Updated collections rows:", cur.rowcount)
conn.close()

# Now test loading collection with ChromaDB client
client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection(name="technical_kb")
print("SUCCESS: Loaded ChromaDB collection:", coll.name, "count:", coll.count())
