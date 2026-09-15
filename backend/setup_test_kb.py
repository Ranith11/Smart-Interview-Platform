import chromadb
from sentence_transformers import SentenceTransformer
import uuid
import os
from app.config import CHROMA_DB_DIR

def setup_test_kb():
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    try:
        client.delete_collection('technical_kb')
    except:
        pass
    collection = client.create_collection('technical_kb')
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    existing_concepts = [
        ("Classes and Objects", "Classes and Objects are the fundamental building blocks of object-oriented programming in Java."),
        ("Inheritance", "Inheritance allows one class to inherit the fields and methods of another class in Java."),
        ("Interfaces", "Interfaces in Java are abstract types used to specify a behavior that classes must implement.")
    ]
    
    for concept, text in existing_concepts:
        emb = model.encode(text, convert_to_numpy=True).tolist()
        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[emb],
            metadatas=[{"domain": "Java", "concept": concept, "source": "test", "source_url": "test"}],
            documents=[text]
        )
    print("Created technical_kb with 3 concepts.")

def setup_test_pdf():
    from reportlab.pdfgen import canvas
    os.makedirs("data/syllabi", exist_ok=True)
    c = canvas.Canvas('data/syllabi/Java.pdf')
    c.drawString(100, 750, 'Java Syllabus Reference')
    
    # 3 existing
    c.drawString(100, 700, 'Classes and Objects are the fundamental building blocks of object-oriented programming in Java.')
    c.drawString(100, 680, 'Inheritance allows one class to inherit the fields and methods of another class in Java.')
    c.drawString(100, 660, 'Interfaces in Java are abstract types used to specify a behavior that classes must implement.')
    
    # 3 new
    c.drawString(100, 640, 'Abstract Classes in Java cannot be instantiated and are used to provide partial implementation.')
    c.drawString(100, 620, 'Generics enable types to be parameters when defining classes, interfaces and methods.')
    c.drawString(100, 600, 'Java Streams represent a sequence of elements supporting sequential and parallel aggregate operations.')
    
    c.save()
    print("Created data/syllabi/Java.pdf with 6 concepts.")

if __name__ == "__main__":
    setup_test_kb()
    setup_test_pdf()
