import sys
sys.path.insert(0, ".")
from app.database import engine
from sqlalchemy import text

def main():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'smartinterview' AND TABLE_NAME = 'resumes' AND COLUMN_NAME = 'name'")).scalar()
        if res == 0:
            conn.execute(text("ALTER TABLE resumes ADD COLUMN name VARCHAR(255) NULL AFTER filename"))
            conn.commit()
            print("Added name column to resumes table successfully!")
        else:
            print("name column already exists in resumes table.")

if __name__ == "__main__":
    main()
