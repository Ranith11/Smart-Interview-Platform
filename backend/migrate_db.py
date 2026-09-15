from sqlalchemy import create_engine, text
engine = create_engine('mysql+pymysql://root:root@localhost:3306/smartinterview')
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN mode VARCHAR(255) DEFAULT 'normal'"))
    except Exception as e: print(e)
    try:
        conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN syllabus_id VARCHAR(255) NULL"))
    except Exception as e: print(e)
    try:
        conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN syllabus_state JSON NULL"))
    except Exception as e: print(e)
    conn.commit()
