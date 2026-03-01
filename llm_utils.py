import requests
from urllib.parse import urljoin
from langchain_ollama import ChatOllama
from typing import Callable, Optional, List
from langchain_core.callbacks.base import BaseCallbackHandler
from config import OLLAMA_BASE_URL


class BufferedStreamingHandler(BaseCallbackHandler):
    def __init__(self, buffer_limit: int = 60, ui_callback: Optional[Callable[[str], None]] = None):
        self.buffer = ""
        self.buffer_limit = buffer_limit
        self.ui_callback = ui_callback

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.buffer += token
        if "\n" in token or len(self.buffer) >= self.buffer_limit:
            print(self.buffer, end="", flush=True)
            if self.ui_callback:
                self.ui_callback(self.buffer)
            self.buffer = ""

    def on_llm_end(self, response, **kwargs) -> None:
        if self.buffer:
            print(self.buffer, end="", flush=True)
            if self.ui_callback:
                self.ui_callback(self.buffer)
            self.buffer = ""


_common_callbacks = [BufferedStreamingHandler(buffer_limit=60)]
_common_llm_params = {
    "temperature": 0,
    "streaming": True,
    "callbacks": _common_callbacks,
}


def _normalize_model_name(name: str) -> str:
    return (name or "").strip().lower()


def _get_ollama_base_url() -> str:
    return OLLAMA_BASE_URL.rstrip("/") + "/"


def fetch_ollama_models() -> List[str]:
    """
    Retrieve locally available Ollama models by querying the Ollama HTTP API.
    Returns an empty list if the API is not reachable.
    """
    base_url = _get_ollama_base_url()

    try:
        resp = requests.get(urljoin(base_url, "api/tags"), timeout=3)
        resp.raise_for_status()
        models = resp.json().get("models", [])

        available = []
        seen = set()
        for model_data in models:
            name = model_data.get("name") or model_data.get("model")
            if not name:
                continue
            normalized = _normalize_model_name(name)
            if normalized in seen:
                continue
            seen.add(normalized)
            available.append(name)
        return available
    except (requests.RequestException, ValueError, AttributeError):
        return []


def get_model_choices() -> List[str]:
    """Return Ollama models available on the configured Ollama instance."""
    return fetch_ollama_models()


def resolve_model_config(model_choice: str):
    """
    Resolve a model choice (case-insensitive) to an Ollama model configuration.
    """
    if not model_choice:
        return None

    model_choice_lower = _normalize_model_name(model_choice)
    for ollama_model in fetch_ollama_models():
        if _normalize_model_name(ollama_model) == model_choice_lower:
            return {
                "class": ChatOllama,
                "constructor_params": {
                    "model": ollama_model,
                    "base_url": OLLAMA_BASE_URL,
                },
            }

    return None
