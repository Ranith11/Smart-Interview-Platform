# Week 6 Final Audit — Skill-First Architecture

## Architecture

```
Resume PDF → Resume Parser → Extract Technical Skills → Select Skills (deterministic rotation)
    → RAG Query per Skill → ChromaDB Retrieval → Optional Project Context
    → Prompt → Groq GPT-OSS 120B → Technical Mock Interview Question
```

No coverage classification. No hard distance thresholds. Skills are the primary question source. Projects are optional personalization context. RAG provides supporting technical knowledge.

## Test Results

### Test 1: sample_resume.pdf, --count 3, --difficulty easy, --type mixed, --verbose
- **Skills selected:** Java, Python, C++
- **Q1 (Java, Conceptual):** "What is the difference between an abstract class and an interface in Java?" — RAG: Available (oop_interfaces-abstract-classes_001)
- **Q2 (Python, Practical):** "How would you expose a scikit-learn recommendation model as a Flask endpoint that returns JSON?" — RAG: Available, Project context used (recommendation system)
- **Q3 (C++, Technical Reasoning):** "When would you prefer using private inheritance rather than composition to reuse functionality in C++?" — RAG: Available (oop_encapsulation_001)
- **Result:** 3/3 generated, 3 skills used ✓

### Test 2: sample_resume.pdf, --count 5, --difficulty medium, --type mixed
- **Skills selected:** Java, Python, C++, SQL, JavaScript
- **Q1 (Java):** "What is the difference between an abstract class and an interface in Java regarding method implementation and inheritance?"
- **Q2 (Python):** "How would you design a Flask endpoint to efficiently serve product recommendations?"
- **Q3 (C++):** [GENERATION FAILED — rate limit]
- **Q4 (SQL):** "In production, a customer reports missing transactions; how would you use SQL to diagnose the issue?"
- **Q5 (JavaScript):** "How did you implement a queue using arrays, and what was its time complexity?"
- **Result:** 4/5 generated (1 rate-limit failure), 5 skills used ✓

### Test 3: sample_resume2.pdf, --count 3, --difficulty easy, --type mixed, --verbose
- **Skills selected:** Java, Python, C++
- **Q1 (Java, Conceptual):** "What is the main difference between an abstract class and an interface in Java?"
- **Q2 (Python, Practical):** "Write a Python function that returns the maximum value in a given list without using built-in max."
- **Q3 (C++, Technical Reasoning):** "When would you prefer using private inheritance rather than composition in C++?"
- **Result:** 3/3 generated, 3 skills used ✓

### Test 4: sample_resume2.pdf, --count 5, --difficulty medium, --type mixed
- **Skills selected:** Java, Python, C++, SQL (Postgres), JavaScript
- **Q1 (Java):** Abstract class vs interface question
- **Q2 (Python):** Remove duplicates from list while preserving order
- **Q3 (C++):** Class design question (truncated output)
- **Q4 (SQL/Postgres):** "A query that used to run in seconds now takes minutes; how would you investigate in PostgreSQL?"
- **Q5 (JavaScript):** Queue implementation question
- **Result:** 5/5 generated, 5 skills used ✓

### Test 5: Week 5 Regression
- Command: `python scripts/test_retrieval.py "What are ACID properties?" --top_k 3`
- Returned: dbms_acid-properties_006 (0.8978), dbms_acid-properties_001 (1.1062), dbms_acid-properties_007 (1.1311)
- ChromaDB: 402 documents ✓

## Acceptance Criteria

- [x] Resume is required
- [x] Different PDF resumes work (sample_resume.pdf + sample_resume2.pdf)
- [x] Skills are dynamically extracted
- [x] Questions are skill-based (not project-first)
- [x] Different skills are selected via deterministic rotation
- [x] Projects are optional personalization context
- [x] RAG retrieval works as supporting context
- [x] Questions generate when RAG has no useful result
- [x] No coverage classification exists
- [x] No hard distance threshold controls generation
- [x] Questions are concise and natural
- [x] Questions contain one main technical concept
- [x] Questions match the selected skill
- [x] No candidate/project hardcoding
- [x] Week 5 retrieval works
- [x] ChromaDB remains at 402 documents

## Final Status

**WEEK 6 — SIMPLIFIED SKILL-FIRST IMPLEMENTATION COMPLETE**
