from typing import Any, Dict

import requests


class OllamaClientError(Exception):
    pass


class OllamaClient:
    def __init__(self, host: str, model: str, timeout: int = 120) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise OllamaClientError("Prompt must not be empty.")

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise OllamaClientError(f"Ollama request failed: {exc}") from exc

        if response.status_code >= 400:
            raise OllamaClientError(
                f"Ollama API error {response.status_code}: {response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise OllamaClientError("Ollama returned invalid JSON.") from exc

        text = str(data.get("response", "")).strip()
        if not text:
            raise OllamaClientError("Ollama returned an empty response.")

        return text
