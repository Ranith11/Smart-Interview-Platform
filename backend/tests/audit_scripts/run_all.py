import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from test_jd_extraction import run_jd_extraction_tests
from test_semantic_matching import run_semantic_matching_tests
from test_adaptive_engine import run_adaptive_engine_tests
from test_regression import run_regression_tests
import asyncio

async def main():
    print("========================================")
    print("STARTING JOB-SPECIFIC AUDIT & TESTS")
    print("========================================")

    all_results = []
    
    # JD Extraction
    try:
        r1 = await run_jd_extraction_tests()
        all_results.extend(r1)
    except Exception as e:
        print(f"Error in extraction tests: {e}")

    # Semantic Matching
    try:
        r2 = run_semantic_matching_tests()
        all_results.extend(r2)
    except Exception as e:
        print(f"Error in semantic matching tests: {e}")

    # Adaptive Engine
    try:
        r3 = run_adaptive_engine_tests()
        all_results.extend(r3)
    except Exception as e:
        print(f"Error in adaptive engine tests: {e}")

    # Regression
    try:
        r4 = run_regression_tests()
        all_results.extend(r4)
    except Exception as e:
        print(f"Error in regression tests: {e}")

    print("\n\n========================================")
    print("FINAL TEST SUMMARY")
    print("========================================")
    
    passed = sum(1 for r in all_results if r[1] == "PASS")
    failed = sum(1 for r in all_results if r[1] == "FAIL")

    for r in all_results:
        status = "✅ PASS" if r[1] == "PASS" else "❌ FAIL"
        print(f"{status} | {r[0]}")
        if r[2]:
             print(f"         └─ {r[2]}")

    print(f"\nTOTAL: {len(all_results)} | PASSED: {passed} | FAILED: {failed}")

if __name__ == "__main__":
    asyncio.run(main())
