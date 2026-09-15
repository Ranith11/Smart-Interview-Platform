import sys, os
# Add backend folder to path
sys.path.insert(0, r"c:\Users\kondu\Downloads\Smart-Interview-main (1)\Smart-Interview-main\backend")

try:
    from app.main import app
    print("OK: app.main")
except Exception as e:
    print(f"FAIL app.main: {e}")

try:
    from app.routers.job_descriptions import router
    print("OK: job_descriptions router")
except Exception as e:
    print(f"FAIL job_descriptions router: {e}")

try:
    from app.services.jd_service import parse_jd_file, map_skills
    print("OK: jd_service")
except Exception as e:
    print(f"FAIL jd_service: {e}")

try:
    from app.models.job_description import JobDescription
    print("OK: JobDescription model")
except Exception as e:
    print(f"FAIL JobDescription: {e}")

print("--- import check complete ---")
