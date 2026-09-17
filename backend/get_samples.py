import sys
import json
sys.path.append('.')
from app.services.question_service import get_chroma_collection

def main():
    coll = get_chroma_collection()
    data = coll.get()
    
    samples = {}
    for doc, meta in zip(data['documents'], data['metadatas']):
        if not meta:
            continue
        src = meta.get('source')
        if src and src not in samples and src not in ['geeksforgeeks', 'tech-interview-handbook', 'syllabus_java_core']:
            samples[src] = doc
            
    print(json.dumps(samples, indent=2))

if __name__ == "__main__":
    main()
