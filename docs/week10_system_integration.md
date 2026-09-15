# Week 10 — System Integration

## Overview

Week 10 integrates the adaptive learning engine (Week 8) and answer evaluation engine (Week 9) into the existing SmartInterview platform, connecting the full stack from React frontend through FastAPI backend to MySQL persistence.

## Full Architecture

```
React Frontend (Vite)
       ↓ Axios
FastAPI Backend
       ↓
┌──────────────────────────────────────────┐
│ Interview Router (interviews.py)         │
│   POST /start → first question           │
│   POST /questions/{id}/answer → evaluate │
│   GET  /{id}/results → rich results      │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│ Interview Service (interview_service.py) │
│   create_interview_session()             │
│   submit_and_evaluate()                  │
│   complete_interview()                   │
│   get_session_results()                  │
└──────────────────────────────────────────┘
       ↓                    ↓
┌─────────────────┐  ┌─────────────────┐
│ Evaluation Svc  │  │ Adaptive Engine │
│ - LLM scoring   │  │ - Bloom levels  │
│ - Semantic sim   │  │ - Score rules   │
│ - Concept cov.  │  │ - Skill select  │
└─────────────────┘  └─────────────────┘
       ↓                    ↓
┌──────────────────────────────────────────┐
│ Question Service (question_service.py)   │
│   generate_single_question()             │
│   RAG retrieval + Groq generation        │
└──────────────────────────────────────────┘
       ↓           ↓           ↓
   ChromaDB    SBERT      Groq API
   (RAG KB)    (Embed)    (LLM)
                              ↓
                         MySQL (persist)
```

## API Endpoints

### Modified Endpoints

| Endpoint | Change |
|----------|--------|
| `POST /api/interviews/start` | Returns session + first question only (not all) |
| `POST /api/interviews/{id}/questions/{question_id}/answer` | Uses database question ID. Returns evaluation + next question |
| `GET /api/interviews/{id}` | Includes adaptive state, bloom levels, evaluations |
| `POST /api/interviews/{id}/complete` | Returns final results with recommendations |

### New Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/interviews/{id}/results` | Rich results: per-skill breakdown, bloom progression, recommendations |
| `GET /api/users/performance` | Aggregated performance across all evaluated interviews |

### Question ID Consistency

The answer endpoint uses the **database question ID** (`InterviewQuestion.id`), NOT the question number. This is consistent across:
- Backend schemas
- Backend router
- Frontend API calls (`/interviews/${id}/questions/${question.id}/answer`)

## Adaptive Interview Flow

```
User clicks "Start Interview"
       ↓
POST /api/interviews/start
       ↓
Backend: create session → init adaptive state → generate Q1
       ↓
Frontend: display Q1 (one question at a time)
       ↓
User writes answer → clicks Submit
       ↓
POST /api/interviews/{id}/questions/{question_id}/answer
       ↓
Backend:
  1. Store answer
  2. Evaluate answer (LLM + semantic similarity)
  3. Store evaluation
  4. Update adaptive state (score-based Bloom progression)
  5. If questions remain: generate next question
  6. If last question: mark complete + generate recommendations
       ↓
Frontend: show evaluation briefly → display next question (or redirect to results)
       ↓
Repeat until all questions answered
       ↓
GET /api/interviews/{id}/results → full results page
```

## Frontend Pages

### Interview.jsx (Modified)
- Displays one question at a time
- Shows Bloom level and difficulty badges
- Submit → shows evaluation overlay (3 seconds) → transitions to next question
- Progress bar tracks questions answered / total
- No backward navigation in adaptive mode
- Handles completion with auto-redirect to results

### Results.jsx (Modified)
- Overall score from actual evaluation data
- Per-skill performance bars
- Bloom progression visualization
- Expandable question-by-question review with score breakdowns
- Recommendations from actual weakness data
- No fake data — empty state when no evaluations

### PerformanceDashboard.jsx (New)
- Route: `/performance`
- Aggregated data across all evaluated interviews
- Overall average, per-skill bars, strengths/weaknesses
- Personalized recommendations from real performance
- Recent interview links with scores
- Meaningful empty state when no data

### Dashboard.jsx (Modified)
- Average score stat card (when available)
- Score display in recent interview list items

### History.jsx (Modified)
- Average score display per interview

### Navbar.jsx (Modified)
- Added "Performance" nav item

### App.jsx (Modified)
- Added `/performance` route

## Database

### Migration: `backend/setup_database_v2.sql`
- Safe to run on existing database (uses INFORMATION_SCHEMA checks)
- Adds columns without dropping data
- Creates `answer_evaluations` table with IF NOT EXISTS
- Idempotent — safe to run multiple times

### Backward Compatibility
- `is_adaptive=NULL/FALSE` sessions use legacy all-questions-upfront behavior
- `is_adaptive=TRUE` sessions use adaptive one-at-a-time flow
- Legacy sessions remain readable in history and results
- No existing data is modified or deleted

## User Workflow

1. Login → Dashboard
2. Upload Resume (if needed) → Skills extracted
3. Interview Setup → Select skills, difficulty, question count
4. Start Adaptive Interview → Q1 generated
5. Answer Q1 → Evaluated → Score shown → Q2 generated (adaptive)
6. Continue until configured question count
7. Results page → Scores, skill breakdown, bloom progression, recommendations
8. Performance Dashboard → Aggregated data across all interviews

## Recommendations

Generated from actual performance data:
- Skills with average < 40 → "high priority, focus on fundamentals"
- Skills with average 40-60 → "medium priority, review core concepts"
- Skills with average 60-80 → "low priority, challenge with complexity"
- Overall low Bloom → "practice application-level problems"

No generic or templated recommendations disconnected from real data.

## Voice/STT Status

**Voice-based interview and Speech-to-Text integration are deferred to Week 11.**

The current interface is entirely text-based. The design supports future voice integration through:
- Separate answer input mechanism (text area can be complemented by audio)
- Evaluation pipeline accepts text input (can receive transcribed text)
- Clean separation of concerns between input, evaluation, and adaptive logic
