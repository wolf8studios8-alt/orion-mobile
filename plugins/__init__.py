"""
plugins/__init__.py — Contrato de plugins de ORION.

Define el protocolo que todo plugin debe cumplir.
No es obligatorio heredar de PluginBase, pero sí tener TOOLS definido.
El loader en agent.py valida esto automáticamente.

ESTRUCTURA MÍNIMA DE UN PLUGIN:
─────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mi_funcion",
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
]

def mi_funcion(param1: str) -> str:
    ...
─────────────────────────────────────────────

Para herramientas ASYNC:
    async def mi_funcion_async(param: str) -> str:
        ...

El loader detecta automáticamente si la función es coroutine.
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class PluginModule(Protocol):
    """
    Protocolo estructural para módulos de plugin.
    No es necesario importarlo en los plugins; es solo para type-checking.
    """
    TOOLS: list[dict]
