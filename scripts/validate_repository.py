import os
import json
import glob
from collections import defaultdict

PROCESSED_DIR = os.path.join("data", "processed")

def check_suspicious_text(text):
    text_lower = text.lower()
    reasons = []
    if not text.strip():
        return ["empty"]
    if len(text.strip()) < 50:
        reasons.append("extremely short")
    # Heading only check (mostly single line, short)
    lines = text.strip().split('\n')
    if len(lines) == 1 and len(text) < 100:
        reasons.append("heading-only")
    
    suspicious_phrases = ["cookie", "advertisement", "subscribe", "login to read", "click here", "sign in", "related articles", "share this", "follow us"]
    for phrase in suspicious_phrases:
        if phrase in text_lower:
            reasons.append(f"contains '{phrase}'")
            
    return reasons

def validate_repository():
    stats = {
        "files": 0,
        "total_chunks": 0,
        "unique_ids": set(),
        "duplicate_ids": defaultdict(list),
        "tokens": [],
        "domains": defaultdict(lambda: defaultdict(int)),
        "issues": []
    }
    
    seen_texts = defaultdict(list)

    if not os.path.exists(PROCESSED_DIR):
        print("ERROR: Processed directory not found.")
        return

    domain_dirs = [d for d in os.listdir(PROCESSED_DIR) if os.path.isdir(os.path.join(PROCESSED_DIR, d))]
    
    for domain in domain_dirs:
        domain_path = os.path.join(PROCESSED_DIR, domain)
        json_files = glob.glob(os.path.join(domain_path, "*_chunks.json"))
        
        for file_path in json_files:
            stats["files"] += 1
            expected_concept = os.path.basename(file_path).replace('_chunks.json', '')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
            except json.JSONDecodeError:
                stats["issues"].append({
                    "file": file_path, "chunk_id": "N/A", "problem": "Invalid JSON", "severity": "ERROR"
                })
                continue
                
            for chunk in chunks:
                stats["total_chunks"] += 1
                chunk_id = chunk.get("chunk_id", "")
                
                # Check 1: Required Fields
                required_fields = ["chunk_id", "domain", "concept", "source", "source_url", "text", "token_count"]
                missing = [f for f in required_fields if not chunk.get(f)]
                if missing:
                    stats["issues"].append({
                        "file": file_path, "chunk_id": chunk_id, "problem": f"Missing/empty fields: {missing}", "severity": "ERROR"
                    })
                
                # Check 2: Token Count
                token_count = chunk.get("token_count")
                if isinstance(token_count, int):
                    stats["tokens"].append(token_count)
                    if token_count < 50 or token_count > 400:
                        stats["issues"].append({
                            "file": file_path, "chunk_id": chunk_id, "problem": f"Token count out of bounds ({token_count})", "severity": "ERROR"
                        })
                else:
                    stats["issues"].append({
                        "file": file_path, "chunk_id": chunk_id, "problem": "Token count is not an integer", "severity": "ERROR"
                    })

                # Check 3: Duplicate IDs
                if chunk_id:
                    if chunk_id in stats["unique_ids"]:
                        stats["duplicate_ids"][chunk_id].append(file_path)
                    else:
                        stats["unique_ids"].add(chunk_id)
                
                # Check 4: Metadata Consistency
                act_domain = chunk.get("domain", "")
                act_concept = chunk.get("concept", "")
                
                if act_domain != domain:
                    stats["issues"].append({
                        "file": file_path, "chunk_id": chunk_id, "problem": f"Domain mismatch: {act_domain} != {domain}", "severity": "WARNING"
                    })
                if act_concept != expected_concept:
                    stats["issues"].append({
                        "file": file_path, "chunk_id": chunk_id, "problem": f"Concept mismatch: {act_concept} != {expected_concept}", "severity": "WARNING"
                    })

                # Check 5: Suspicious Content
                text = chunk.get("text", "")
                suspicious = check_suspicious_text(text)
                if suspicious:
                    stats["issues"].append({
                        "file": file_path, "chunk_id": chunk_id, "problem": f"Suspicious text: {', '.join(suspicious)}", "severity": "WARNING"
                    })

                # Check 6: Duplicate Text
                if text:
                    seen_texts[text].append((file_path, chunk_id))
                
                # Inventory
                if act_domain and act_concept:
                    stats["domains"][act_domain][act_concept] += 1

    # Finalize Duplicates
    for text, occurrences in seen_texts.items():
        if len(occurrences) > 1:
            locs = [f"{os.path.basename(o[0])} ({o[1]})" for o in occurrences]
            stats["issues"].append({
                "file": "Multiple", "chunk_id": "Multiple", "problem": f"Exact duplicate text found in: {', '.join(locs)}", "severity": "WARNING"
            })
            
    for chunk_id, files in stats["duplicate_ids"].items():
        stats["issues"].append({
            "file": ", ".join([os.path.basename(f) for f in files]), "chunk_id": chunk_id, "problem": "Duplicate Chunk ID", "severity": "ERROR"
        })

    # Print Report
    print("="*50)
    print("REPOSITORY STATISTICS")
    print("="*50)
    print(f"JSON files: {stats['files']}")
    print(f"Domains: {len(stats['domains'])}")
    print(f"Concepts: {sum(len(c) for c in stats['domains'].values())}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Unique chunk IDs: {len(stats['unique_ids'])}")
    if stats['tokens']:
        print(f"Average tokens: {sum(stats['tokens']) / len(stats['tokens']):.2f}")
        print(f"Minimum tokens: {min(stats['tokens'])}")
        print(f"Maximum tokens: {max(stats['tokens'])}")

    print("\n" + "="*50)
    print("DOMAIN BREAKDOWN")
    print("="*50)
    for dom in sorted(stats['domains'].keys()):
        print(f"\n{dom.upper()}")
        for conc in sorted(stats['domains'][dom].keys()):
            print(f"  {conc}: {stats['domains'][dom][conc]}")

    print("\n" + "="*50)
    print("ISSUES DETECTED")
    print("="*50)
    if not stats["issues"]:
        print("No issues detected.")
    else:
        for issue in stats["issues"]:
            print(f"[{issue['severity']}] {issue['file']} | {issue['chunk_id']} | {issue['problem']}")

if __name__ == "__main__":
    validate_repository()
