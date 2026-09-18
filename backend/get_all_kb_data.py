import chromadb
import json
import os

def dump_kb_to_json():
    # Point this to where the chroma_db folder is located
    db_path = r"c:\Users\user\Desktop\Smart-Interview-main\chroma_db"
    out_file = r"c:\Users\user\Desktop\Smart-Interview-main\backend\kb_data_dump.json"

    print(f"Connecting to ChromaDB at {db_path}...")
    client = chromadb.PersistentClient(path=db_path)

    # Get the main knowledge base collection
    collection = client.get_collection(name="technical_kb")

    # Retrieve all data
    all_data = collection.get(include=["documents", "metadatas"])
    
    total_items = len(all_data['ids'])
    print(f"Retrieved {total_items} items. Formatting data...")

    formatted_data = []
    
    for i in range(total_items):
        item = {
            "id": all_data['ids'][i],
            "metadata": all_data['metadatas'][i],
            "document": all_data['documents'][i]
        }
        formatted_data.append(item)

    print(f"Writing data to {out_file}...")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully saved all {total_items} items to {out_file}")

if __name__ == "__main__":
    dump_kb_to_json()
