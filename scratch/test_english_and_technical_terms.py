"""
Test English-Only Enforcement and Technical Term Phonetic Normalization
"""

import sys
import os
import io

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.services.voice_service import normalize_technical_transcription, transcribe_audio_bytes, synthesize_speech_bytes
import asyncio

def test_normalization():
    print("=" * 60)
    print("  TESTING TECHNICAL TERM PHONETIC NORMALIZATION")
    print("=" * 60)

    # 1. Test Arabic / Urdu Script Stripping
    arabic_input = "\u0645\u0631\u062d\u0628\u0627 In Python we use GIL and FastAPI"
    cleaned = normalize_technical_transcription(arabic_input)
    print("\n[1] Foreign script test:")
    print("  Cleaned:", cleaned)
    assert "\u0645\u0631\u062d\u0628\u0627" not in cleaned
    assert "GIL" in cleaned and "FastAPI" in cleaned

    # 2. Test Phonetic Technical Term Mapping
    test_cases = [
        ("in see plus plus we use v tables and dynamic dispatch", ["C++", "vtable"]),
        ("we query sequel and postgres for relational data", ["SQL", "PostgreSQL"]),
        ("secure the rest api with j w t and o auth 2", ["REST API", "JWT", "OAuth 2.0"]),
        ("containerize with dock er and deploy on cooper neties", ["Docker", "Kubernetes"]),
        ("python multithreading is constrained by g i l", ["Python", "GIL"]),
        ("we use b trees for database indexing", ["B-tree"]),
        ("the endpoint is written with fast api using async and await", ["FastAPI", "async/await"]),
    ]

    print("\n[2] Phonetic mapping tests:")
    for spoken, expected in test_cases:
        res = normalize_technical_transcription(spoken)
        print(f"  Spoken:  '{spoken}'")
        print(f"  Result:  '{res}'")
        for term in expected:
            assert term in res, f"Expected '{term}' in '{res}'"
        print(f"  [PASS] Successfully normalized to {expected}")

    # 3. Test Full Audio STT with strict English decoding
    print("\n[3] Testing Audio STT with strict English language decoding...")
    audio_text = "In Python, the Global Interpreter Lock limits multithreading, while FastAPI and PostgreSQL handle backend services."
    audio_bytes = asyncio.run(synthesize_speech_bytes(audio_text))
    
    transcript = transcribe_audio_bytes(audio_bytes, filename="answer.webm", mime_type="audio/webm")
    print("  Synthesized Text:", audio_text)
    print("  Transcribed STT: ", transcript)
    assert "Python" in transcript
    assert "FastAPI" in transcript
    assert "PostgreSQL" in transcript
    # Verify no non-ASCII / Arabic script exists
    assert all(ord(c) < 128 or c in "‘’“”–—" for c in transcript), "Transcription must be strictly English!"
    print("  [PASS] Audio decoded strictly in English with technical term accuracy!")

    print("\n" + "=" * 60)
    print("  ALL ENGLISH AND TECHNICAL NORMALIZATION TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_normalization()
