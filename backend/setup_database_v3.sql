-- ============================================================
-- SmartInterview — Database Migration v3 (Infinite Adaptive)
-- ============================================================
-- Adds completion_reason for open-ended adaptive interviews.
-- SAFE to run on existing database. Does not drop data.
-- ============================================================

USE smartinterview;

-- Add completion_reason column if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'completion_reason');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN completion_reason VARCHAR(50) NULL',
    'SELECT "completion_reason already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Done
SELECT 'Migration v3 complete — Infinite Adaptive schema applied.' AS status;
