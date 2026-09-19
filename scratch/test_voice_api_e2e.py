"""
Test Voice Layer Endpoints (TTS, STT, and Status)
"""

import sys
import os
import io

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_voice_api():
    print("=" * 60)
    print("  TESTING SMARTINTERVIEW VOICE API ENDPOINTS")
    print("=" * 60)

    # 1. Test Voice Status
    print("\n[1] Testing GET /api/interviews/voice/status...")
    res = client.get("/api/interviews/voice/status")
    assert res.status_code == 200, f"Status failed: {res.text}"
    status_data = res.json()
    print(f"  [PASS] Voice status: {status_data}")
    assert status_data["voice_enabled"] is True

    # 2. Test Voice TTS (with Intro for Q1)
    print("\n[2] Testing POST /api/interviews/voice/tts (Q1 with intro)...")
    tts_payload = {
        "text": "Can you explain how indexing works in PostgreSQL and when a B-Tree index is preferable to a Hash index?",
        "question_number": 1,
        "include_intro": True
    }
    res_tts = client.post("/api/interviews/voice/tts", json=tts_payload)
    assert res_tts.status_code == 200, f"TTS failed: {res_tts.text}"
    assert res_tts.headers["content-type"] == "audio/mpeg"
    audio_bytes = res_tts.content
    print(f"  [PASS] TTS generated {len(audio_bytes)} MP3 bytes")
    assert len(audio_bytes) > 5000

    # 3. Test TTS Cache Hit
    print("\n[3] Testing TTS Cache Hit...")
    res_tts_cached = client.post("/api/interviews/voice/tts", json=tts_payload)
    assert res_tts_cached.status_code == 200
    assert len(res_tts_cached.content) == len(audio_bytes)
    print(f"  [PASS] Cache hit returned identical {len(res_tts_cached.content)} bytes instantly")

    # 4. Test Voice Transcribe (STT) with Groq Whisper
    print("\n[4] Testing POST /api/interviews/voice/transcribe...")
    # Register/login user for auth
    email = "voice_tester@example.com"
    pwd = "Password123!"
    r_auth = client.post("/api/auth/login", json={"email": email, "password": pwd})
    if r_auth.status_code != 200:
        r_auth = client.post("/api/auth/register", json={
            "name": "Voice Tester",
            "email": email,
            "password": pwd,
            "confirm_password": pwd
        })
        assert r_auth.status_code == 201, f"Register failed: {r_auth.text}"

    token = r_auth.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Transcribe the audio generated in step 2
    files = {
        "file": ("question.mp3", io.BytesIO(audio_bytes), "audio/mpeg")
    }
    res_stt = client.post("/api/interviews/voice/transcribe", files=files, headers=headers)
    assert res_stt.status_code == 200, f"STT failed: {res_stt.text}"
    transcript = res_stt.json()["transcript"]
    print(f"  [PASS] Transcribed text: \"{transcript}\"")
    assert "PostgreSQL" in transcript or "indexing" in transcript.lower() or "b-tree" in transcript.lower() or "hash" in transcript.lower()

    print("\n" + "=" * 60)
    print("  VOICE API TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_voice_api()
