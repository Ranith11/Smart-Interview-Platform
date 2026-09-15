-- ============================================================
-- SmartInterview — Database Migration v2 (Weeks 8-10)
-- ============================================================
-- This migration adds adaptive learning and evaluation tables/columns.
-- It is SAFE to run on an existing database — it does NOT drop any tables or data.
-- It uses INFORMATION_SCHEMA checks to avoid errors if columns already exist.
-- ============================================================

USE smartinterview;

-- ── 1. Add Bloom columns to interview_questions ──────────────

-- Add bloom_level column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_questions'
    AND COLUMN_NAME = 'bloom_level');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_questions ADD COLUMN bloom_level VARCHAR(20) NULL',
    'SELECT "bloom_level already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add bloom_level_number column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_questions'
    AND COLUMN_NAME = 'bloom_level_number');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_questions ADD COLUMN bloom_level_number INT NULL',
    'SELECT "bloom_level_number already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


-- ── 2. Add adaptive columns to interview_sessions ────────────

-- Add is_adaptive column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'is_adaptive');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN is_adaptive TINYINT(1) NULL DEFAULT 1',
    'SELECT "is_adaptive already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add adaptive_state column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'adaptive_state');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN adaptive_state JSON NULL',
    'SELECT "adaptive_state already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add current_bloom_level column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'current_bloom_level');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN current_bloom_level VARCHAR(20) NULL',
    'SELECT "current_bloom_level already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add final_recommendations column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'final_recommendations');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN final_recommendations JSON NULL',
    'SELECT "final_recommendations already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


-- ── 3. Create answer_evaluations table ───────────────────────

CREATE TABLE IF NOT EXISTS answer_evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    answer_id INT NOT NULL UNIQUE,
    question_id INT NOT NULL,

    technical_score INT NOT NULL DEFAULT 0,
    completeness_score INT NOT NULL DEFAULT 0,
    relevance_score INT NOT NULL DEFAULT 0,
    semantic_similarity_score INT NOT NULL DEFAULT 0,
    concept_coverage_score INT NOT NULL DEFAULT 0,
    overall_score INT NOT NULL DEFAULT 0,

    feedback TEXT NULL,
    strengths JSON NULL,
    weaknesses JSON NULL,
    concepts_expected JSON NULL,
    concepts_found JSON NULL,

    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Done ─────────────────────────────────────────────────────
SELECT 'Migration v2 complete — Weeks 8-10 schema applied.' AS status;
