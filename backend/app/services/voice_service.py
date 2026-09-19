"""
SmartInterview — Voice Service
Provides Speech-to-Text (STT) and Text-to-Speech (TTS) integration.

STT:
- Powered by Groq Cloud Whisper (whisper-large-v3)
- Features domain-primed technical vocabulary prompting to ensure high recognition accuracy
  for programming languages, frameworks, cloud tooling, algorithms, and technical acronyms
- Audio is processed directly in-memory as a byte stream; candidate audio is NEVER stored permanently
- Zero disk footprint, preserving candidate privacy

TTS:
- Powered by high-fidelity Microsoft Neural TTS (edge-tts)
- Professional, calm, natural voice tailored for technical interviews (en-US-ChristopherNeural)
- In-memory SHA-256 LRU cache for near-instant audio replay
- Dynamic text normalization for spoken interview delivery (strips markdown, formatting artifacts)
"""

import re
import io
import hashlib
import asyncio
from typing import Optional
from groq import Groq
from app.config import GROQ_API_KEY

# ── Technical Vocabulary Prompt for Whisper ──────────────────────────
# Groq Whisper requires prompt <= 896 characters (224 tokens).
# Contains high-density technical keywords and acronyms to prime the decoder.
TECHNICAL_VOCABULARY_PROMPT = (
    "Technical interview response: Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust, "
    "SQL, PostgreSQL, MySQL, MongoDB, Redis, SQLite, React, Node.js, FastAPI, Django, "
    "REST, GraphQL, gRPC, API, HTTP, HTTPS, JWT, OAuth, Docker, Kubernetes, CI/CD, Git, GitHub, "
    "OOP, polymorphism, inheritance, encapsulation, abstraction, dynamic dispatch, "
    "DSA, hash map, binary tree, graph, DFS, BFS, dynamic programming, time complexity, "
    "multithreading, concurrency, deadlock, mutex, semaphore, async, await, event loop, GIL, "
    "ACID, normalization, indexing, RAG, LLM, vector database, ChromaDB, microservices."
)

DEFAULT_VOICE = "en-US-ChristopherNeural"

# In-memory LRU cache for synthesized audio: {sha256_hash: bytes}
_TTS_CACHE: dict[str, bytes] = {}
_MAX_CACHE_SIZE = 150

_groq_client: Optional[Groq] = None


def _get_groq_client() -> Groq:
    """Lazy initialize the Groq client for Whisper STT."""
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def clean_text_for_speech(text: str) -> str:
    """
    Normalizes written text so it is spoken naturally by the TTS engine.
    Removes markdown ticks, bold/italic asterisks, bullet points, and code markers
    while preserving natural technical pronunciation and sentence cadence.
    """
    if not text:
        return ""

    # Remove Markdown headings
    clean = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # Remove bold/italic markdown (* or _)
    clean = re.sub(r"[\*_]{1,3}([^*_]+)[\*_]{1,3}", r"\1", clean)

    # Remove code blocks and inline code markers
    clean = re.sub(r"```[\w]*\n(.*?)```", r"\1", clean, flags=re.DOTALL)
    clean = re.sub(r"`([^`]+)`", r"\1", clean)

    # Remove markdown link formatting [text](url) -> text
    clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)

    # Remove markdown list bullets
    clean = re.sub(r"^\s*[-*+]\s+", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^\s*\d+\.\s+", "", clean, flags=re.MULTILINE)

    # Normalize multiple whitespace and linebreaks into clean conversational pauses
    clean = re.sub(r"\n+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    return clean


async def synthesize_speech_bytes(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """
    Synthesize natural speech from text using edge-tts.
    Returns in-memory MP3 bytes with caching.
    """
    cleaned = clean_text_for_speech(text)
    if not cleaned:
        cleaned = "Could you please tell me about your technical background and experience?"

    # Check cache
    cache_key = hashlib.sha256(f"{voice}:{cleaned}".encode("utf-8")).hexdigest()
    if cache_key in _TTS_CACHE:
        return _TTS_CACHE[cache_key]

    import edge_tts

    communicate = edge_tts.Communicate(cleaned, voice)
    audio_buffer = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.extend(chunk["data"])

    audio_bytes = bytes(audio_buffer)

    # Cache result in memory
    if len(_TTS_CACHE) >= _MAX_CACHE_SIZE:
        # Evict one key (simple eviction)
        _TTS_CACHE.pop(next(iter(_TTS_CACHE)))
    _TTS_CACHE[cache_key] = audio_bytes

    return audio_bytes


def get_interview_intro() -> str:
    """Natural, calm, professional introduction for Question 1."""
    return (
        "Hello! Welcome to your technical interview. "
        "I will be guiding you through a series of technical questions today. "
        "You can respond naturally using your microphone, or by typing your answer in the box. "
        "Let's get started."
    )


async def generate_question_speech(
    question_text: str,
    question_number: int = 1,
    include_intro: bool = False,
    voice: str = DEFAULT_VOICE,
) -> bytes:
    """
    Prepares and synthesizes audio for an interview question.
    If include_intro is True (or question_number == 1 with explicit flag),
    prepends a polite professional welcome before the first question.
    """
    speech_text = question_text
    if include_intro and question_number == 1:
        speech_text = f"{get_interview_intro()} {question_text}"

    return await synthesize_speech_bytes(speech_text, voice=voice)


def normalize_technical_transcription(text: str) -> str:
    """
    Sanitizes STT transcription:
    1. Enforces pure English output: strips any accidental Arabic, Urdu, or non-Latin script.
    2. Maps spoken technical phonetics to canonical engineering terms, code keywords, and acronyms.
    """
    if not text:
        return ""

    # Strip any accidental non-Latin or Arabic/Urdu/Persian script
    text = re.sub(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+", "", text)

    # Technical acronym and phonetic mappings (case-insensitive)
    patterns = [
        # Languages & Frameworks
        (r"\b(?:see\s*plus\s*plus|c\s*plus\s*plus)\b", "C++"),
        (r"\b(?:see\s*sharp|c\s*sharp)\b", "C#"),
        (r"\b(?:fast\s*api)\b", "FastAPI"),
        (r"\b(?:node\s*js)\b", "Node.js"),
        (r"\b(?:next\s*js)\b", "Next.js"),
        (r"\b(?:pie\s*thon|python)\b", "Python"),
        (r"\b(?:type\s*script)\b", "TypeScript"),
        (r"\b(?:java\s*script)\b", "JavaScript"),
        (r"\b(?:java)\b", "Java"),
        (r"\b(?:golang)\b", "Go"),
        
        # Databases & Formats
        (r"\b(?:postgres|post\s*gres|postgress)\b", "PostgreSQL"),
        (r"\b(?:mongo\s*db)\b", "MongoDB"),
        (r"\b(?:sequel|s\s*q\s*l)\b", "SQL"),
        (r"\b(?:no\s*sql)\b", "NoSQL"),
        (r"\b(?:sqlite|sequel\s*lite)\b", "SQLite"),
        
        # Web & Protocols
        (r"\b(?:rest\s*apis?)\b", "REST API"),
        (r"\b(?:rest\s*ful)\b", "RESTful"),
        (r"\b(?:j\s*w\s*t|jay\s*son\s*web\s*tokens?|json\s*web\s*tokens?)\b", "JWT"),
        (r"\b(?:o\s*auth\s*2|oauth\s*2)\b", "OAuth 2.0"),
        (r"\b(?:o\s*auth)\b", "OAuth"),
        (r"\b(?:g\s*r\s*p\s*c)\b", "gRPC"),
        (r"\b(?:graph\s*ql)\b", "GraphQL"),
        (r"\b(?:http\s*s)\b", "HTTPS"),
        (r"\b(?:http)\b", "HTTP"),
        
        # DevOps & Cloud
        (r"\b(?:k\s*8\s*s|cooper\s*neties|cubernetes)\b", "Kubernetes"),
        (r"\b(?:dock\s*er)\b", "Docker"),
        (r"\b(?:git\s*hub)\b", "GitHub"),
        (r"\b(?:ci\s*cd|c\s*i\s*c\s*d)\b", "CI/CD"),
        
        # CS Core, Concurrency, Architecture
        (r"\b(?:g\s*i\s*l)\b", "GIL"),
        (r"\b(?:o\s*o\s*p)\b", "OOP"),
        (r"\b(?:d\s*s\s*a)\b", "DSA"),
        (r"\b(?:r\s*a\s*g)\b", "RAG"),
        (r"\b(?:l\s*l\s*ms?)\b", "LLM"),
        (r"\b(?:a\s*c\s*i\s*d)\b", "ACID"),
        (r"\b(?:v\s*tables?)\b", "vtable"),
        (r"\b(?:b\s*trees?)\b", "B-tree"),
        (r"\b(?:async\s*and\s*await|async\s*await)\b", "async/await"),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    mime_type: str = "audio/webm",
) -> str:
    """
    Transcribe raw microphone audio bytes using Groq Whisper.
    Uses in-memory file tuple to avoid saving raw audio to disk.
    Applies technical vocabulary prompting for high precision.
    Enforces strict English decoding (language='en') and technical term normalization.
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return ""

    client = _get_groq_client()

    # Groq accepts in-memory tuple: (filename, bytes, content_type)
    file_tuple = (filename, audio_bytes, mime_type)

    raw_text = ""
    try:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=file_tuple,
            language="en",
            prompt=TECHNICAL_VOCABULARY_PROMPT,
            temperature=0.0,
            response_format="json",
        )
        raw_text = (transcription.text or "").strip()
    except Exception as e:
        # If webm container header failed with Whisper, try generic name with language='en'
        if "audio.webm" in filename:
            try:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=("recording.wav", audio_bytes, "audio/wav"),
                    language="en",
                    prompt=TECHNICAL_VOCABULARY_PROMPT,
                    temperature=0.0,
                    response_format="json",
                )
                raw_text = (transcription.text or "").strip()
            except Exception:
                raise e
        else:
            raise e

    return normalize_technical_transcription(raw_text)
