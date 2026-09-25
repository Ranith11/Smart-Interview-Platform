# Workspace Guidelines & Mandatory Rules

## 1. Automatic Deliverables Synchronization & Conflict Verification
Whenever any code changes, feature extensions, API modifications, or database updates are implemented in this repository:
- **Never modify** the finalized frozen files in `SmartInterview_Deliverables/`.
- **Progressively update** the active versioned copies in `SmartInterview_Progressive_Updates/`:
  1. **SRS Specification**: `SmartInterview_Progressive_Updates/02_SRS_Specification/SmartInterview_SRS_Template_Format_v2.docx` (and `.pdf`)
  2. **Presentation PPT**: `SmartInterview_Progressive_Updates/04_Presentation_and_Defense/SmartInterview_Project_Presentation_v2.pptx` (and `.pdf`)
  3. **Research Paper**: `SmartInterview_Progressive_Updates/03_Research_Paper/SmartInterview_Research_Paper_v2.docx` (and `.pdf`, `_IEEE_v2.md`)
  4. **Master Encyclopedia & Viva Defense**: `SmartInterview_Progressive_Updates/01_Documentation_and_Viva/SmartInterview_Master_Encyclopedia_and_Viva_Defense_v2.md` (and `.docx`, `.pdf`)
- **Execute Cross-Document Verification**:
  - Always verify that newly added features and existing data are accurate against actual code implementation.
  - Ensure zero conflicts or contradictions across SRS, PPT, Research Paper, Master Encyclopedia, and codebase.
  - Include relevant architecture/UML diagrams and visual assets.
  - Run `python scripts/verify_deliverables_sync.py` to confirm harmony.
- **Remind the User**:
  - Remind the user about the synchronized updates, verified points, and document statuses in the final response.
