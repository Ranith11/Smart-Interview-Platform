import argparse
import chromadb
from sentence_transformers import SentenceTransformer

def test_retrieval(query, domain_filter=None, top_k=5):
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_collection(name="technical_kb")
    
    print(f"\nEmbedding query: '{query}'")
    query_embedding = model.encode(query, convert_to_numpy=True).tolist()
    
    where_clause = {}
    if domain_filter:
        where_clause["domain"] = domain_filter
        print(f"Applying metadata filter: domain='{domain_filter}'")
        
    print(f"Retrieving top {top_k} results...\n")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause if where_clause else None
    )
    
    if not results['ids'][0]:
        print("No results found.")
        return
        
    for i in range(len(results['ids'][0])):
        chunk_id = results['ids'][0][i]
        distance = results['distances'][0][i] if results['distances'] else "N/A"
        metadata = results['metadatas'][0][i]
        text = results['documents'][0][i]
        
        print("-" * 40)
        print(f"Rank: {i + 1}")
        print(f"Distance/Similarity: {distance}")
        print(f"Chunk ID: {chunk_id}")
        print(f"Domain: {metadata.get('domain', 'N/A')}")
        print(f"Concept: {metadata.get('concept', 'N/A')}")
        print(f"Source: {metadata.get('source', 'N/A')}")
        print(f"Source URL: {metadata.get('source_url', 'N/A')}")
        print("\nText:")
        print(text[:300] + "..." if len(text) > 300 else text)
        print("-" * 40 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RAG Retrieval")
    parser.add_argument("query", type=str, help="The query string")
    parser.add_argument("--domain", type=str, help="Filter by domain", default=None)
    parser.add_argument("--top_k", type=int, help="Number of results to retrieve", default=5)
    
    args = parser.parse_args()
    test_retrieval(args.query, args.domain, args.top_k)
