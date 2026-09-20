import sys
import os
import io
import asyncio
from fastapi import UploadFile

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.routers.interviews import extract_jd_file

def _create_upload_file(filename, content_bytes):
    from starlette.datastructures import Headers
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content_bytes),
        headers=Headers({"content-type": "application/octet-stream"})
    )

async def run_jd_extraction_tests():
    print("--- Running JD Extraction Tests ---")
    results = []

    # 1. TXT test
    try:
        txt_content = b"This is a test job description.\nWe need Python and Docker."
        f = _create_upload_file("test.txt", txt_content)
        res = await extract_jd_file(file=f, current_user=None)
        if "Python and Docker" in res["extracted_text"]:
            results.append(("TXT Extraction", "PASS", ""))
        else:
            results.append(("TXT Extraction", "FAIL", "Text not found"))
    except Exception as e:
        results.append(("TXT Extraction", "FAIL", str(e)))

    # 2. Empty TXT Test
    try:
        f = _create_upload_file("empty.txt", b"")
        res = await extract_jd_file(file=f, current_user=None)
        results.append(("Empty TXT", "FAIL", "Should have raised exception"))
    except Exception as e:
        if "empty" in str(e).lower():
            results.append(("Empty TXT", "PASS", ""))
        else:
            results.append(("Empty TXT", "FAIL", str(e)))

    # 3. PDF Test
    try:
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text(pymupdf.Point(50, 50), "Senior Backend Engineer.\nRequired: Python, AWS.")
        pdf_bytes = doc.write()
        doc.close()
        
        f = _create_upload_file("test.pdf", pdf_bytes)
        res = await extract_jd_file(file=f, current_user=None)
        if "Senior Backend Engineer" in res["extracted_text"]:
            results.append(("PDF Extraction", "PASS", ""))
        else:
            results.append(("PDF Extraction", "FAIL", "Text not found"))
    except Exception as e:
        results.append(("PDF Extraction", "FAIL", str(e)))

    # 4. Scanned PDF (Empty Text) Test
    try:
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        # insert no text, maybe an image or just blank
        pdf_bytes = doc.write()
        doc.close()
        
        f = _create_upload_file("scanned.pdf", pdf_bytes)
        res = await extract_jd_file(file=f, current_user=None)
        results.append(("Scanned PDF Detection", "FAIL", "Should have raised exception"))
    except Exception as e:
        if "scanned" in str(e).lower():
            results.append(("Scanned PDF Detection", "PASS", ""))
        else:
            results.append(("Scanned PDF Detection", "FAIL", str(e)))

    return results

if __name__ == "__main__":
    res = asyncio.run(run_jd_extraction_tests())
    for r in res:
        print(f"[{r[1]}] {r[0]}: {r[2]}")
