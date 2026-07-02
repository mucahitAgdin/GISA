from dataclasses import dataclass
from typing import Optional
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    github_token: Optional[str]
    ollama_model: str
    ollama_host: str


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("GITHUB_TOKEN", "").strip()

    return Settings(
        github_token=token or None,
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b").strip(),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").strip(),
    )
