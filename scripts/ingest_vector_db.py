import os
import json
import glob
import chromadb
from sentence_transformers import SentenceTransformer

PROCESSED_DIR = os.path.join("data", "processed")
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "technical_kb"

def ingest():
    print("Initializing embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print(f"Connecting to ChromaDB at {CHROMA_DB_DIR}...")
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Track existing IDs for idempotency check logging
    existing_count = collection.count()
    print(f"Collection '{COLLECTION_NAME}' currently has {existing_count} documents.")
    
    json_files = glob.glob(os.path.join(PROCESSED_DIR, "**", "*_chunks.json"), recursive=True)
    
    total_files = len(json_files)
    total_chunks_found = 0
    skipped_chunks = 0
    upserted_chunks = 0
    
    documents = []
    metadatas = []
    ids = []
    
    print(f"Found {total_files} JSON files to process.")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
            
        for chunk in chunks:
            total_chunks_found += 1
            
            # Validate required fields
            req_fields = ["chunk_id", "domain", "concept", "source", "source_url", "text", "token_count"]
            if not all(chunk.get(f) for f in req_fields):
                skipped_chunks += 1
                continue
                
            chunk_id = chunk["chunk_id"]
            text = chunk["text"]
            
            # Prepare metadata
            metadata = {
                "domain": chunk["domain"],
                "concept": chunk["concept"],
                "source": chunk["source"],
                "source_url": chunk["source_url"],
                "token_count": chunk["token_count"]
            }
            
            documents.append(text)
            metadatas.append(metadata)
            ids.append(chunk_id)
            upserted_chunks += 1
            
    if not documents:
        print("No valid chunks found to ingest.")
        return
        
    print(f"Generating embeddings for {len(documents)} chunks...")
    embeddings = model.encode(documents, convert_to_numpy=True).tolist()
    
    print(f"Upserting {len(documents)} documents to ChromaDB...")
    
    # Batch upsert to handle limits (Chroma default max batch size is typically large enough for 400, but let's be safe)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            documents=documents[i:i+batch_size]
        )
        
    final_count = collection.count()
    
    print("\n" + "="*50)
    print("INGESTION RESULTS")
    print("="*50)
    print(f"JSON files processed: {total_files}")
    print(f"Total chunks found:   {total_chunks_found}")
    print(f"Chunks skipped:       {skipped_chunks}")
    print(f"Chunks upserted:      {upserted_chunks}")
    print(f"Final ChromaDB count: {final_count}")
    print("="*50)

if __name__ == "__main__":
    ingest()
