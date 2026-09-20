-- ============================================================
-- SmartInterview — Database Migration v4 (Job-Specific Mode)
-- ============================================================
-- Adds job_description_text, job_description_title, and
-- job_relevance_data columns for Job-Specific interviews.
-- SAFE to run on existing database. Does not drop data.
-- ============================================================

USE smartinterview;

-- Add job_description_text column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'job_description_text');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN job_description_text TEXT NULL',
    'SELECT "job_description_text already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add job_description_title column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'job_description_title');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN job_description_title VARCHAR(500) NULL',
    'SELECT "job_description_title already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add job_relevance_data column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'job_relevance_data');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN job_relevance_data JSON NULL',
    'SELECT "job_relevance_data already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Done
SELECT 'Migration v4 complete — Job-Specific Mode schema applied.' AS status;
