-- ============================================================
-- SmartInterview — Database Migration v4 (Job Description)
-- ============================================================
-- Adds job_descriptions table and job_description_id in interview_sessions.
-- SAFE to run on existing database. Does not drop data.
-- ============================================================

USE smartinterview;

CREATE TABLE IF NOT EXISTS job_descriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    skills JSON,
    raw_text MEDIUMTEXT,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add job_description_id to interview_sessions if not exists
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'smartinterview'
    AND TABLE_NAME = 'interview_sessions'
    AND COLUMN_NAME = 'job_description_id');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE interview_sessions ADD COLUMN job_description_id INT NULL, ADD CONSTRAINT fk_interview_sessions_jd FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL',
    'SELECT "job_description_id already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Migration v4 complete — Job Description schema applied.' AS status;
