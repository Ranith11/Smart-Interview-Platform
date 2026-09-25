# AUTOMATIC DELIVERABLES SYNCHRONIZATION & CONFLICT VERIFICATION RULE

## 1. MANDATORY CONTEXT & TRIGGER
Whenever any progress, code modifications, feature implementations, API updates, or database schema changes occur in this repository:
You **MUST AUTOMATICALLY** update the progressive deliverable files even if the user does NOT explicitly ask or forgets to mention it.

## 2. STRICT RULES FOR FILES & VERSIONS
1. **NEVER MODIFY FINALIZED DELIVERABLES**:
   The files inside `SmartInterview_Deliverables/` are frozen baseline submissions. NEVER edit, overwrite, or delete them.
2. **ACTIVE PROGRESSIVE WORKING COPIES**:
   Always apply progressive updates to the versioned files located in `SmartInterview_Progressive_Updates/`:
   - **SRS Specification**: `SmartInterview_Progressive_Updates/02_SRS_Specification/SmartInterview_SRS_Template_Format_v2.docx` (and export to `.pdf`)
   - **Project Presentation PPT**: `SmartInterview_Progressive_Updates/04_Presentation_and_Defense/SmartInterview_Project_Presentation_v2.pptx` (and export to `.pdf`)
   - **Research Paper**: `SmartInterview_Progressive_Updates/03_Research_Paper/SmartInterview_Research_Paper_v2.docx` (and `.pdf`, `_IEEE_v2.md`)
   - **Master Encyclopedia & Viva Defense**: `SmartInterview_Progressive_Updates/01_Documentation_and_Viva/SmartInterview_Master_Encyclopedia_and_Viva_Defense_v2.md` (and `.docx`, `.pdf`)

## 3. COMPREHENSIVE VERIFICATION PROTOCOL (ZERO CONFLICTS)
Before declaring any update complete, you **MUST**:
1. **Verify All Technical Metrics Against Active Code**:
   - Bloom's Taxonomy Cognitive Levels & State Machine progression.
   - Scoring equations & Multi-factor weights.
   - Vector database specifications: ChromaDB collections, embeddings model (`all-MiniLM-L6-v2`), similarity thresholds.
   - LLM models: Groq Cloud models (`openai/gpt-oss-120b`, fallback `openai/gpt-oss-20b`).
   - Database schema: Tables, foreign keys, relationships in MySQL/SQLite.
   - FastAPI routers & REST API contracts.
2. **Regression Check (New AND Existing Data)**:
   - Verify that new additions do NOT contradict existing claims, figures, tables, or sections across any of the 4 documents.
   - Cross-check that terms, metrics, and architecture diagrams match identically between SRS, PPT, Research Paper, and Master Encyclopedia.
3. **Include & Verify Images**:
   - Ensure all diagrams (`Architecture.png`, `ERD.png`, `Workflow.png`, UML diagrams) and visual screenshots are embedded, referenced, and up-to-date in DOCX, PPTX, and PDF outputs.
4. **Automated Verification**:
   - Run `python scripts/verify_deliverables_sync.py` to ensure zero discrepancies.

## 4. MANDATORY REMINDER TO USER
At the end of your response after making updates, you **MUST** provide an explicit reminder summary to the user:
- Details of the progressive deliverables updated (`_v2` files).
- List of verified technical parameters (both new and existing).
- Confirmation that no conflicts exist across documents.
- Confirmation that the frozen baseline in `SmartInterview_Deliverables/` was preserved.
