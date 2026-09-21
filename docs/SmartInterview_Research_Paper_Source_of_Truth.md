# SmartInterview: Research Paper Source of Truth
**Title:** SmartInterview: An Adaptive, RAG-Powered Framework for Dynamic Technical Mock Interviews using Multi-Signal Evaluation

## Abstract
Traditional mock interview platforms rely on static question banks and subjective LLM evaluations. We present SmartInterview, a novel framework that integrates Retrieval-Augmented Generation (RAG) with a deterministic adaptive engine based on Bloom’s Taxonomy. To overcome the unreliability of zero-shot LLM evaluation, we propose a multi-signal scoring system combining semantic embeddings (`all-MiniLM-L6-v2`), concept coverage algorithms, and Groq-accelerated LLM reasoning.

## 1. Introduction
The gap between technical candidate preparation and actual industry interview standards is widening. Current AI interviewers fail in three areas: (1) hallucinating technically inaccurate questions, (2) relying purely on LLM "vibes" for scoring, and (3) failing to adapt cognitive complexity to the user's real-time skill level. SmartInterview addresses these by grounding the AI in a verified ChromaDB vector space and orchestrating the session via a rigid state machine.

## 2. Methodology & System Architecture
### 2.1 Intersection-Driven Skill Extraction
Unlike generic interviewers, SmartInterview requires both a candidate Resume and a target Job Description (JD). The system extracts skills using PyMuPDF and computes a priority matrix (Group A: Overlapping Skills, Group B: JD-Only Skills) to guarantee relevance.

### 2.2 Deterministic Adaptive Engine
We reject LLM-driven flow control due to unpredictability. Instead, SmartInterview uses a deterministic Python engine tracking a 6-stage progression of Bloom's Taxonomy (Remember → Understand → Apply → Analyze → Evaluate → Create). An answer scoring ≥80% triggers an upward state transition, while <50% triggers regression, dynamically controlling the prompt parameters for the next generation cycle.

### 2.3 Multi-Signal Evaluation Framework
Relying solely on LLMs to output a score out of 100 is empirically flawed. We designed a robust evaluation pipeline:
1. **Semantic Grounding**: The LLM extracts the "Expected Concepts" for a perfect answer.
2. **Embeddings**: We encode both the candidate's answer and the expected concepts using `all-MiniLM-L6-v2`.
3. **Similarity Calculation**: Cosine similarity is computed. If the semantic distance is too high, the LLM's subjective score is penalized.
4. **Final Computation**: The final score is a weighted average of LLM subjective metrics (Technical, Completeness, Relevance) and objective geometric metrics (Semantic Similarity, Concept Coverage).

## 3. Implementation Details
The backend is built on FastAPI and MySQL, leveraging Groq's Inference API (`openai/gpt-oss-120b`) for rapid generation. Voice features utilize Microsoft Neural TTS (`edge-tts`) and Groq Whisper, executed entirely in-memory to reduce latency. The frontend is a React 18 SPA utilizing Tailwind CSS for modern glassmorphic UI design.

## 4. Conclusion
SmartInterview demonstrates that combining strict deterministic state machines with high-speed LLMs and RAG yields a superior, fairer, and more accurate technical mock interview experience compared to pure-prompting approaches.
