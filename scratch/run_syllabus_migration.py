import pymysql

def run_migration():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Root@1234',
        database='smartinterview',
        autocommit=True
    )
    with conn.cursor() as cur:
        # Check existing columns
        cur.execute("DESCRIBE interview_sessions;")
        existing_cols = {row[0] for row in cur.fetchall()}
        
        if "mode" not in existing_cols:
            print("Adding column 'mode'...")
            cur.execute("ALTER TABLE interview_sessions ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'normal';")
        else:
            print("Column 'mode' already exists.")

        if "syllabus_id" not in existing_cols:
            print("Adding column 'syllabus_id'...")
            cur.execute("ALTER TABLE interview_sessions ADD COLUMN syllabus_id VARCHAR(100) NULL;")
        else:
            print("Column 'syllabus_id' already exists.")

        if "syllabus_state" not in existing_cols:
            print("Adding column 'syllabus_state'...")
            cur.execute("ALTER TABLE interview_sessions ADD COLUMN syllabus_state JSON NULL;")
        else:
            print("Column 'syllabus_state' already exists.")

    conn.close()
    print("Syllabus database migration completed successfully!")

if __name__ == "__main__":
    run_migration()
