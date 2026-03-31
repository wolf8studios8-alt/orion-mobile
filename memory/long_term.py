"""
memory/long_term.py — Memoria persistente a largo plazo.

CORRECCIÓN vs. versión original:
  - Ruta relativa al proyecto (no hardcodeada a C:\\Users\\Francisco\\...)
  - Función delete_memory añadida
  - Logging en lugar de print
  - Manejo de errores explícito
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("orion.memory")

# Ruta relativa: memory/user_data.json (junto a este mismo archivo)
_MEMORY_DIR = Path(__file__).resolve().parent
_MEMORY_FILE = _MEMORY_DIR / "user_data.json"


def load_memory() -> dict:
    """Carga la memoria completa. Devuelve {} si no existe o está corrupta."""
    if not _MEMORY_FILE.exists():
        return {}
    try:
        with open(_MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error("[Memory] user_data.json corrupto: %s", e)
        return {}
    except OSError as e:
        logger.error("[Memory] No se pudo leer la memoria: %s", e)
        return {}


def save_memory(key: str, value: str) -> str:
    """Guarda un par clave-valor en la memoria persistente."""
    data = load_memory()
    data[key] = value
    try:
        _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("[Memory] Guardado: %s = %s", key, value)
        return f"Recordado: tu {key} es {value}."
    except OSError as e:
        logger.error("[Memory] Error al guardar: %s", e)
        return f"Error al guardar en memoria: {e}"


def delete_memory(key: str) -> str:
    """Elimina una clave de la memoria."""
    data = load_memory()
    if key not in data:
        return f"No tengo '{key}' en memoria."
    del data[key]
    try:
        with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return f"Olvidado: {key}."
    except OSError as e:
        return f"Error al actualizar memoria: {e}"
