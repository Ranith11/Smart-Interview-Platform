-- ============================================================
-- SmartInterview — Database Migration v5 (Resume Candidate Name)
-- ============================================================
-- Adds candidate name column to resumes table.
-- SAFE to run on existing database. Does not drop data.
-- ============================================================

USE smartinterview;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'resumes'
    AND COLUMN_NAME = 'name');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE resumes ADD COLUMN name VARCHAR(255) NULL AFTER filename',
    'SELECT "resumes.name already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Migration v5 complete — Resume Candidate Name applied.' AS status;
