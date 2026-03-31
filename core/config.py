"""
core/config.py — Singleton de configuración.
Lee config.json UNA sola vez y lo expone en todo el proyecto.
Elimina la duplicación en AudioEngine y OrionAgent.
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("orion.config")

_BASE_DIR = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _BASE_DIR / "config.json"

_DEFAULTS: dict[str, Any] = {
    "ai_name": "ORION",
    "llm_model": "llama-3.3-70b-versatile",
    "stt_model": "whisper-large-v3-turbo",
    "voice_id": "pFZP5JQG7iQjIQuC4Bku",
    "mic_threshold": 450,
    "language": "es",
    "max_history_messages": 20,   # ventana deslizante de historial
}

class _Config:
    """Singleton de configuración. Accede via `get_config()`."""
    _instance: "_Config | None" = None
    _data: dict[str, Any] = {}

    def __new__(cls) -> "_Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        self._data = dict(_DEFAULTS)
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                loaded = json.load(f)
            self._data.update(loaded)
            logger.info("[Config] Cargado correctamente desde %s", _CONFIG_PATH)
        except FileNotFoundError:
            logger.warning("[Config] config.json no encontrado, usando valores por defecto.")
        except json.JSONDecodeError as e:
            logger.error("[Config] JSON inválido: %s — usando valores por defecto.", e)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    @property
    def base_dir(self) -> Path:
        return _BASE_DIR


def get_config() -> _Config:
    """Punto de acceso global al singleton de configuración."""
    return _Config()
