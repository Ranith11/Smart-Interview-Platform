import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            skills JSON,
            raw_text MEDIUMTEXT,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """))
    
    # Check if job_description_id column exists
    res = conn.execute(text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'smartinterview'
        AND TABLE_NAME = 'interview_sessions'
        AND COLUMN_NAME = 'job_description_id'
    """)).scalar()
    
    if res == 0:
        conn.execute(text("""
            ALTER TABLE interview_sessions 
            ADD COLUMN job_description_id INT NULL, 
            ADD CONSTRAINT fk_interview_sessions_jd 
            FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL
        """))
        print("Column job_description_id added to interview_sessions")
    else:
        print("Column job_description_id already exists")
        
    conn.commit()
    print("Database migration v4 applied successfully.")
