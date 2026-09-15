import json
import chromadb
from sentence_transformers import SentenceTransformer

def evaluate_retrieval():
    print("Loading queries...")
    with open("data/evaluation/retrieval_queries.json", "r", encoding="utf-8") as f:
        queries = json.load(f)
        
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_collection(name="technical_kb")
    
    total_queries = len(queries)
    hits_1 = 0
    hits_3 = 0
    hits_5 = 0
    mrr_sum = 0.0
    
    failed_queries = []
    
    for item in queries:
        q_text = item["query"]
        expected_domain = item["expected_domain"]
        expected_concept = item["expected_concept"]
        
        query_embedding = model.encode(q_text, convert_to_numpy=True).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        # Results are lists of lists
        if not results['metadatas'][0]:
            failed_queries.append({"query": q_text, "reason": "No results returned"})
            continue
            
        metadatas = results['metadatas'][0]
        
        # Find rank of first correct chunk
        first_correct_rank = -1
        for i, meta in enumerate(metadatas):
            if meta.get("domain") == expected_domain and meta.get("concept") == expected_concept:
                first_correct_rank = i + 1
                break
                
        if first_correct_rank != -1:
            if first_correct_rank == 1:
                hits_1 += 1
            if first_correct_rank <= 3:
                hits_3 += 1
            if first_correct_rank <= 5:
                hits_5 += 1
            mrr_sum += (1.0 / first_correct_rank)
        else:
            retrieved_concepts = [f"{m.get('domain')}/{m.get('concept')}" for m in metadatas]
            failed_queries.append({
                "query": q_text,
                "expected": f"{expected_domain}/{expected_concept}",
                "retrieved_top5": retrieved_concepts
            })
            
    # Calculate metrics
    hit1_score = (hits_1 / total_queries) * 100
    hit3_score = (hits_3 / total_queries) * 100
    hit5_score = (hits_5 / total_queries) * 100
    mrr_score = mrr_sum / total_queries
    
    print("\n" + "="*50)
    print("EVALUATION METRICS")
    print("="*50)
    print(f"Total Queries: {total_queries}")
    print(f"Hit@1: {hit1_score:.2f}%")
    print(f"Hit@3: {hit3_score:.2f}%")
    print(f"Hit@5: {hit5_score:.2f}%")
    print(f"MRR:   {mrr_score:.4f}")
    print(f"Recall@5: {hit5_score:.2f}%") # In this context, Recall@5 is equivalent to Hit@5 since we just want to find relevant concepts
    
    print("\n" + "="*50)
    print("FAILED QUERIES (Not in Top 5)")
    print("="*50)
    if not failed_queries:
        print("None! All queries found their expected concepts in the top 5.")
    else:
        for fq in failed_queries:
            print(f"Q: {fq['query']}")
            print(f"Expected: {fq['expected']}")
            print(f"Retrieved: {fq['retrieved_top5']}\n")

if __name__ == "__main__":
    evaluate_retrieval()
