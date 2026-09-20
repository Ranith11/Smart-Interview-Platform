"""Run database migration v4 — Add JD columns to interview_sessions."""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = 'smartinterview' AND TABLE_NAME = 'interview_sessions' "
        "ORDER BY ORDINAL_POSITION"
    ))
    existing = [row[0] for row in result]
    print("Existing columns:", existing)

    migrations = [
        ("job_description_text", "TEXT NULL"),
        ("job_description_title", "VARCHAR(500) NULL"),
        ("job_relevance_data", "JSON NULL"),
    ]

    for col_name, col_def in migrations:
        if col_name not in existing:
            conn.execute(text(f"ALTER TABLE interview_sessions ADD COLUMN {col_name} {col_def}"))
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column already exists: {col_name}")

    conn.commit()

    result2 = conn.execute(text(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = 'smartinterview' AND TABLE_NAME = 'interview_sessions' "
        "ORDER BY ORDINAL_POSITION"
    ))
    final = [row[0] for row in result2]
    print("Final columns:", final)

print("Migration v4 complete.")
