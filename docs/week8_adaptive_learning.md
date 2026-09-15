# Week 8 — Adaptive Learning Engine

## Overview

Week 8 introduces Bloom's Taxonomy and an adaptive learning engine that controls interview question progression based on candidate performance. The engine makes **deterministic decisions** — the LLM does NOT decide progression.

## Bloom's Taxonomy

Six cognitive levels are used, ordered from simple to complex:

| Order | Level      | Description                                          |
|-------|------------|------------------------------------------------------|
| 1     | Remember   | Recall facts, definitions, terminology               |
| 2     | Understand | Explain concepts, summarize, interpret               |
| 3     | Apply      | Use knowledge in practical situations                |
| 4     | Analyze    | Compare, break down, identify relationships          |
| 5     | Evaluate   | Judge, justify decisions, critique solutions          |
| 6     | Create     | Design, propose, architect new solutions             |

### Boundaries
- Never goes below **Remember** (level 1)
- Never exceeds **Create** (level 6)

### Implementation
File: `backend/app/services/bloom.py`

- `BloomLevel` — frozen dataclass with `id`, `name`, `order`, `description`, `question_guidance`
- `get_bloom_level(identifier)` — lookup by string id or numeric order
- `next_level(current)` — returns next level, or None at max
- `prev_level(current)` — returns previous level, or None at min
- `clamp_bloom_order(order)` — clamps to valid bounds [1, 6]

## Adaptive Algorithm

File: `backend/app/services/adaptive_engine.py`

### Score-Based Progression Rules

These rules are **deterministic Python logic**, not LLM decisions:

| Score Range | Action                                                             |
|-------------|---------------------------------------------------------------------|
| ≥ 80        | Advance Bloom level. If already at Create, advance difficulty.     |
| 50–79       | Maintain current level (no change).                                |
| < 50        | Regress Bloom level. If at Remember, lower difficulty if possible. |

### Difficulty Levels
- `easy` → `medium` → `hard`
- Never creates invalid difficulty values

### Examples
```
Remember + score 90 → Understand
Understand + score 85 → Apply
Apply + score 45 → Understand  (regress)
Remember + score 30 → Remember, easy  (reinforce + lower difficulty)
Create + score 95 → Create, hard  (advance difficulty instead)
```

## Learner Profile

`SkillPerformance` tracks per-skill:
- `attempts` — number of questions answered
- `total_score` — sum of evaluation scores
- `average_score` — calculated property
- `current_bloom_order` — current Bloom level for this skill
- `current_difficulty` — current difficulty for this skill
- `scores` — list of all scores

## Skill Selection

`select_skill()` uses **weakness-biased round-robin**:
1. Find skills with fewest attempts
2. Among equally-attempted, pick weakest (lowest average score)
3. Ensures all skills get coverage while weak skills get more attention

Example:
```
Java = 85 avg (2 attempts)
SQL = 45 avg (1 attempt)
Python = 91 avg (2 attempts)
→ SQL selected (fewer attempts AND weakest)
```

## Question Type Selection

Bloom level guides question type selection, but is NOT a rigid 1:1 mapping:

| Bloom Level | Suitable Types (ordered by preference)            |
|-------------|---------------------------------------------------|
| Remember    | conceptual, practical, technical_reasoning         |
| Understand  | conceptual, technical_reasoning, practical         |
| Apply       | practical, conceptual, scenario                    |
| Analyze     | technical_reasoning, practical, scenario           |
| Evaluate    | scenario, technical_reasoning, project             |
| Create      | project, scenario, practical                       |

## Adaptive State

`AdaptiveState` is serialized as JSON and stored in `interview_sessions.adaptive_state`:
- `selected_skills` — skills chosen for this interview
- `question_count` — total questions requested
- `questions_generated` / `questions_answered` — progress tracking
- `current_skill` / `current_bloom_id` / `current_difficulty` / `current_question_type`
- `skill_performances` — per-skill tracking data
- `previous_questions` — deduplication list

## Database Changes

### Modified: `interview_sessions`
- `is_adaptive` (BOOLEAN) — distinguishes adaptive from legacy sessions
- `adaptive_state` (JSON) — serialized AdaptiveState
- `current_bloom_level` (VARCHAR) — current Bloom level id
- `final_recommendations` (JSON) — generated at completion

### Modified: `interview_questions`
- `bloom_level` (VARCHAR) — Bloom level id for this question
- `bloom_level_number` (INT) — Bloom level order (1–6)

### New: `answer_evaluations`
Stores structured evaluation results per answer. See Week 9 documentation.

All new columns are **nullable** for backward compatibility with existing Week 7 sessions.

## Voice/STT Status

**Voice-based interview and Speech-to-Text integration are deferred to Week 11.**
