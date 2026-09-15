import os
import sys
import io
import chromadb
from contextlib import redirect_stdout

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.syllabus_rag_service import create_temporary_rag, merge_temporary_to_permanent, delete_temporary_rag
from app.config import CHROMA_DB_DIR

def generate_long_pdf():
    from reportlab.pdfgen import canvas
    os.makedirs("data/syllabi", exist_ok=True)
    c = canvas.Canvas('data/syllabi/Java.pdf')
    
    # 7 Concepts with enough text to force multiple chunks
    concepts = [
        ("Classes and Objects", "Classes and Objects are the fundamental building blocks of object-oriented programming in Java. A class is a blueprint from which individual objects are created. " * 30),
        ("Inheritance", "Inheritance allows one class to inherit the fields and methods of another class in Java. It supports the concept of hierarchical classification. " * 30),
        ("Interfaces", "Interfaces in Java are abstract types used to specify a behavior that classes must implement. They are similar to protocols. " * 30),
        ("Abstract Classes", "Abstract Classes in Java cannot be instantiated and are used to provide partial implementation. They can have both abstract and concrete methods. " * 30),
        ("Generics", "Generics enable types to be parameters when defining classes, interfaces and methods. This allows for type-safe collections. " * 30),
        ("Java Streams", "Java Streams represent a sequence of elements supporting sequential and parallel aggregate operations. They are not data structures. " * 30),
        ("Multithreading", "Multithreading is a Java feature that allows concurrent execution of two or more parts of a program for maximum utilization of CPU. " * 30)
    ]
    
    y = 800
    for title, text in concepts:
        c.drawString(50, y, title)
        # Just write a substring to ensure it fills some space, ReportLab drawString doesn't wrap easily
        # Actually it's easier to just write long lines, chunk_text doesn't care about pdf layout, it just extracts text.
        for i in range(0, len(text), 100):
            y -= 15
            c.drawString(50, y, text[i:i+100])
            if y < 100:
                c.showPage()
                y = 800
        y -= 30
        if y < 100:
            c.showPage()
            y = 800
            
    c.save()
    print("Generated data/syllabi/Java.pdf with long texts.")

def run_test():
    generate_long_pdf()
    
    session_id = 999
    print("\n--- 1. RAG Creation ---")
    create_temporary_rag(session_id, "java_core")
    
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    temp_col = client.get_collection(f"temp_syllabus_{session_id}")
    perm_col = client.get_collection("technical_kb")
    
    temp_data = temp_col.get()
    print(f"Temporary RAG created with {len(temp_data['ids'])} chunks.")
    print("Concepts extracted by LLM:")
    for m in temp_data['metadatas']:
        print(" -", m.get("concept"))
        
    perm_count_before = perm_col.count()
    print(f"\nPermanent KB count BEFORE merge: {perm_count_before}")
    
    print("\n--- 2. First Merge ---")
    f1 = io.StringIO()
    with redirect_stdout(f1):
        merge_temporary_to_permanent(session_id)
    output1 = f1.getvalue()
    print(output1)
    
    perm_count_after = perm_col.count()
    added_first = perm_count_after - perm_count_before
    print(f"Permanent KB count AFTER merge: {perm_count_after}")
    print(f"New concepts/chunks added: {added_first}")
    
    print("\n--- 3. Second Merge (Idempotency) ---")
    f2 = io.StringIO()
    with redirect_stdout(f2):
        merge_temporary_to_permanent(session_id)
    output2 = f2.getvalue()
    print(output2)
    
    perm_count_final = perm_col.count()
    added_second = perm_count_final - perm_count_after
    print(f"Permanent KB count AFTER second merge: {perm_count_final}")
    print(f"New concepts/chunks added in second merge: {added_second}")
    
    print("\n--- 4. Cleanup ---")
    delete_temporary_rag(session_id)
    collections = [c.name for c in client.list_collections()]
    if f"temp_syllabus_{session_id}" not in collections:
        print("Temporary collection successfully deleted.")
    else:
        print("Failed to delete temporary collection.")
        
    if "technical_kb" in collections:
        print("Permanent technical_kb still exists.")
    else:
        print("Permanent technical_kb was deleted!")

if __name__ == "__main__":
    run_test()
