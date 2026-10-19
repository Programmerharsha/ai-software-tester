"""
Ollama HTTP client — wraps the local Ollama REST API.
Never changes MODEL_NAME silently; always reads from config.
"""

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Generator, Optional, Tuple
from urllib.parse import urlparse

import requests

from config import OLLAMA_URL, MODEL_NAME, AI_TEMPERATURE, AI_NUM_CTX, AI_TIMEOUT
from database import database as db

_ollama_last_start_attempt = 0.0
_ollama_start_lock = threading.Lock()


def _ollama_base_url() -> str:
    configured_url = db.get_setting("ollama_url", OLLAMA_URL)
    # Accept both the server root and a pasted API root. Appending /api below
    # must never produce /api/api/... .
    base_url = (configured_url or OLLAMA_URL).strip().rstrip("/")
    if base_url.lower().endswith("/api"):
        base_url = base_url[:-4].rstrip("/")
    return base_url


def _configured_model() -> str:
    return (db.get_setting("ai_model", MODEL_NAME) or MODEL_NAME).strip() or MODEL_NAME


def _start_local_ollama(base_url: str) -> bool:
    """Start local Ollama when needed and wait briefly for its API to be ready."""
    global _ollama_last_start_attempt
    host = (urlparse(base_url).hostname or "").lower()
    if host not in {"localhost", "127.0.0.1", "::1"}:
        return False

    with _ollama_start_lock:
        now = time.monotonic()
        if now - _ollama_last_start_attempt < 20:
            return False
        _ollama_last_start_attempt = now

    executable = shutil.which("ollama")
    if not executable and os.name == "nt":
        installed = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        if installed.is_file():
            executable = str(installed)
    if not executable:
        return False

    try:
        options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                   "stderr": subprocess.DEVNULL, "close_fds": True}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            options["start_new_session"] = True
        subprocess.Popen([executable, "serve"], **options)
    except (OSError, subprocess.SubprocessError):
        return False

    # Ollama can take several seconds to bind its port, especially on a cold
    # start. Poll the health API instead of retrying the user request too soon.
    health_url = f"{base_url}/api/tags"
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try:
            response = requests.get(health_url, timeout=0.75)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return True  # launched; the normal request retry reports a useful failure if needed


def _ollama_request(method: str, path: str, **kwargs):
    """Try both /api and no-prefix Ollama endpoints."""
    base_url = _ollama_base_url()
    candidates = [f"{base_url}/api{path}", f"{base_url}{path}"]
    # On Windows, localhost can resolve to IPv6 while Ollama is bound only to
    # IPv4. Retry the same request over loopback IPv4 after a connection error.
    if "localhost" in base_url.lower():
        candidates.extend(url.replace("localhost", "127.0.0.1") for url in tuple(candidates))
    last_exception = None
    last_response = None

    # First attempt normal requests. If the local server is down, start it and
    # retry once after a short boot window. This also runs for the sidebar check.
    for attempt in range(2):
        last_exception = None
        last_response = None
        for url in candidates:
            try:
                r = requests.request(method, url, **kwargs)
                if r.status_code == 404:
                    last_response = r
                    continue
                return r
            except requests.ConnectionError as e:
                last_exception = e
        if attempt == 0 and last_exception is not None and _start_local_ollama(base_url):
            time.sleep(2)
            continue
        break

    if last_response is not None:
        return last_response
    if last_exception is not None:
        raise last_exception
    raise RuntimeError("Ollama request failed")


# ── Health checks ─────────────────────────────────────────────────────────────

def check_ollama_running() -> Tuple[bool, str]:
    """Returns (ok, message)."""
    try:
        r = _ollama_request("GET", "/tags", timeout=5)
        if r.status_code == 200:
            return True, "Ollama is running"
        if r.status_code == 404:
            return False, "Ollama responded with 404. Check your endpoint URL and Ollama version."
        return False, f"Unexpected status: {r.status_code}"
    except requests.ConnectionError:
        return False, "Cannot connect to Ollama (is it running?)"
    except requests.Timeout:
        return False, "Ollama connection timed out"
    except Exception as e:
        return False, str(e)


def check_model_available(model: Optional[str] = None) -> Tuple[bool, str]:
    """Returns (ok, message)."""
    model = model or _configured_model()
    try:
        r = _ollama_request("GET", "/tags", timeout=5)
        if r.status_code != 200:
            return False, "Cannot list models"
        data = r.json()
        models = [m["name"] for m in data.get("models", [])]
        # Match the exact model tag first, then allow a variant suffix that keeps
        # the same model tag (for example qwen2.5-coder:7b-instruct-q4_K_M).
        # Do not treat a different tag (for example qwen2.5-coder:3b) as the same model.
        exact = [m for m in models if m == model]
        tagged_variant = [m for m in models if m.startswith(f"{model}-") or m.startswith(f"{model}:")]
        if exact or tagged_variant:
            found = exact[0] if exact else tagged_variant[0]
            return True, f"Model available: {found}"
        return False, f"Model '{model}' not found. Run: ollama pull {model}"
    except Exception as e:
        return False, str(e)


def get_ai_status() -> Dict:
    from ai import providers
    provider = providers.get_active_provider()

    if provider == "ollama":
        ok_ollama, msg_ollama = check_ollama_running()
        if not ok_ollama:
            return {
                "ollama": False,
                "model": False,
                "ollama_msg": msg_ollama,
                "model_msg": "",
                "provider": "ollama",
                "provider_display": providers.PROVIDER_DISPLAY_NAMES.get("ollama", "Ollama"),
                "ready": False,
            }
        ok_model, msg_model = check_model_available()
        return {
            "ollama": ok_ollama,
            "model": ok_model,
            "ollama_msg": msg_ollama,
            "model_msg": msg_model,
            "configured_model": _configured_model(),
            "provider": "ollama",
            "provider_display": providers.PROVIDER_DISPLAY_NAMES.get("ollama", "Ollama"),
            "ready": ok_ollama and ok_model,
        }

    elif provider == "gemini":
        key = providers.get_provider_api_key("gemini")
        model = providers.get_provider_model("gemini")
        ready = bool(key)
        return {
            "ollama": True,
            "model": ready,
            "ollama_msg": "Google Gemini Cloud Active" if ready else "API Key missing",
            "model_msg": f"Model: {model}",
            "configured_model": model,
            "provider": "gemini",
            "provider_display": providers.PROVIDER_DISPLAY_NAMES.get("gemini", "Google Gemini"),
            "ready": ready,
            "key_configured": bool(key),
        }

    elif provider == "groq":
        key = providers.get_provider_api_key("groq")
        model = providers.get_provider_model("groq")
        ready = bool(key)
        return {
            "ollama": True,
            "model": ready,
            "ollama_msg": "Groq Cloud Inference Active" if ready else "API Key missing",
            "model_msg": f"Model: {model}",
            "configured_model": model,
            "provider": "groq",
            "provider_display": providers.PROVIDER_DISPLAY_NAMES.get("groq", "Groq Cloud"),
            "ready": ready,
            "key_configured": bool(key),
        }

    elif provider == "openai":
        key = providers.get_provider_api_key("openai")
        model = providers.get_provider_model("openai")
        ready = bool(key)
        return {
            "ollama": True,
            "model": ready,
            "ollama_msg": "OpenAI / Custom Endpoint Active" if ready else "API Key missing",
            "model_msg": f"Model: {model}",
            "configured_model": model,
            "provider": "openai",
            "provider_display": providers.PROVIDER_DISPLAY_NAMES.get("openai", "OpenAI / Custom"),
            "ready": ready,
            "key_configured": bool(key),
        }

    else:  # "demo" mode
        return {
            "ollama": True,
            "model": True,
            "ollama_msg": "Built-in Smart Heuristic Engine (Offline / Demo)",
            "model_msg": "Instant In-Memory AI Synthesis (No API Key Required)",
            "configured_model": "smart-heuristic-v1",
            "provider": "demo",
            "provider_display": providers.PROVIDER_DISPLAY_NAMES.get("demo", "Smart Demo Engine"),
            "ready": True,
        }


# ── Chat completion ───────────────────────────────────────────────────────────

def chat(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    temperature: float = AI_TEMPERATURE,
    stream: bool = False,
) -> str:
    """Send a chat message and return the full response string."""
    from ai import providers
    provider = providers.get_active_provider()

    # Route cloud and demo providers to provider engine
    if provider != "ollama":
        return providers.chat_provider(
            prompt=prompt,
            system=system,
            model=model,
            temperature=temperature,
        )

    # Local / remote Ollama execution
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or _configured_model(),
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_ctx": AI_NUM_CTX,
        },
    }

    t0 = time.time()
    try:
        r = _ollama_request(
            "POST",
            "/chat",
            json=payload,
            timeout=AI_TIMEOUT,
            stream=stream,
        )
        r.raise_for_status()
    except requests.Timeout:
        raise RuntimeError(f"Ollama request timed out after {AI_TIMEOUT}s")
    except requests.ConnectionError:
        raise RuntimeError("Cannot reach Ollama. Make sure it is running or switch to Cloud / Demo AI in Settings.")
    except requests.HTTPError as e:
        raise RuntimeError(f"Ollama HTTP error: {e}")

    if stream:
        collected = []
        for line in r.iter_lines():
            if line:
                chunk = json.loads(line)
                collected.append(chunk.get("message", {}).get("content", ""))
                if chunk.get("done"):
                    break
        return "".join(collected)

    data = r.json()
    return data.get("message", {}).get("content", "")


def chat_stream(prompt: str, system: str = "", model: Optional[str] = None) -> Generator[str, None, None]:
    """Streaming version — yields content chunks."""
    from ai import providers
    provider = providers.get_active_provider()

    if provider != "ollama":
        # Yield the generated text as a single or small chunks
        full_res = providers.chat_provider(prompt=prompt, system=system, model=model)
        yield full_res
        return

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or _configured_model(),
        "messages": messages,
        "stream": True,
        "options": {"temperature": AI_TEMPERATURE, "num_ctx": AI_NUM_CTX},
    }

    with _ollama_request(
        "POST",
        "/chat",
        json=payload,
        timeout=AI_TIMEOUT,
        stream=True,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done"):
                    break
