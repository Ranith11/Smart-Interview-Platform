"""
SmartInterview — Unified & Resilient LLM Client Provider
Supports:
1. Cloud Groq (openai/gpt-oss-120b, llama-3.3-70b-versatile, etc.)
2. Local Ollama (llama3.1, mistral, etc. for 100% offline air-gapped mode)
3. Automatic Failover: Falls back to local Ollama if internet drops during live interview.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from app.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_FALLBACK_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)

class OllamaChoice:
    def __init__(self, content: str):
        self.message = type("Msg", (), {"content": content})()
        self.finish_reason = "stop"

class OllamaChatResponse:
    def __init__(self, content: str):
        self.choices = [OllamaChoice(content)]

class OllamaClient:
    """Lightweight, zero-dependency OpenAI-compatible wrapper for local Ollama."""
    def __init__(self, base_url: str = OLLAMA_BASE_URL, default_model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.chat = type("Chat", (), {"completions": type("Completions", (), {"create": self.create})()})()

    def create(
        self,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> OllamaChatResponse:
        target_model = self.default_model
        payload = {
            "model": target_model,
            "messages": messages or [],
            "options": {"temperature": temperature},
            "stream": False
        }
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return OllamaChatResponse(content)
        except Exception as e:
            print(f"[OllamaClient] Error querying local Ollama ({target_model}): {e}")
            raise e

class ResilientLLMClient:
    """Wraps Groq with automatic local Ollama fallback if offline or connection fails."""
    def __init__(self, groq_client: Any, ollama_client: OllamaClient):
        self.groq_client = groq_client
        self.ollama_client = ollama_client
        self.chat = type("Chat", (), {"completions": type("Completions", (), {"create": self.create})()})()

    def create(self, model: str, messages: List[Dict[str, str]], **kwargs):
        provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
        if provider == "ollama":
            return self.ollama_client.create(model=OLLAMA_MODEL, messages=messages, **kwargs)
        
        try:
            if self.groq_client:
                return self.groq_client.chat.completions.create(model=model, messages=messages, **kwargs)
            else:
                raise ValueError("Groq client not initialized.")
        except Exception as groq_err:
            print(f"[ResilientLLMClient] ⚠️ Cloud Groq call failed ({groq_err}). Triggering automatic offline fallback to local Ollama ({OLLAMA_MODEL})...")
            try:
                return self.ollama_client.create(model=OLLAMA_MODEL, messages=messages, **kwargs)
            except Exception as ollama_err:
                print(f"[ResilientLLMClient] ❌ Local Ollama fallback also failed: {ollama_err}")
                raise groq_err

_singleton_client = None

def get_universal_llm_client():
    """Returns the unified LLM client configured per LLM_PROVIDER."""
    global _singleton_client
    if _singleton_client is not None:
        return _singleton_client

    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    ollama_cli = OllamaClient(base_url=OLLAMA_BASE_URL, default_model=OLLAMA_MODEL)

    if provider == "ollama":
        print(f"[LLM] Active Provider: LOCAL OLLAMA ({OLLAMA_MODEL}) [100% Offline Mode]")
        _singleton_client = ollama_cli
        return _singleton_client

    # Initialize Groq client with resilient local fallback
    raw_groq = None
    if GROQ_API_KEY:
        try:
            from groq import Groq
            raw_groq = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            print(f"[LLM] Warning: Could not initialize Groq SDK: {e}")
    
    print(f"[LLM] Active Provider: CLOUD GROQ ({GROQ_MODEL}) with Local Ollama ({OLLAMA_MODEL}) fallback")
    _singleton_client = ResilientLLMClient(groq_client=raw_groq, ollama_client=ollama_cli)
    return _singleton_client

def get_universal_model_name():
    """Returns the active model name based on provider."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    if provider == "ollama":
        return OLLAMA_MODEL
    return GROQ_MODEL
