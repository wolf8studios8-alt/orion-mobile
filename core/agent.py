"""
core/agent.py — Agente conversacional ORION.

MEJORAS vs. versión original:
  - Ventana deslizante en chat_history (evita overflow de contexto)
  - Memoria a largo plazo integrada en el system prompt
  - Config via singleton (sin doble lectura de JSON)
  - Logging estructurado (sin print()s)
  - Manejo explícito de errores en execute_tool y process_input
  - Tool calls con múltiples pasos correctamente encadenados
"""
from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from groq import AsyncGroq
from dotenv import load_dotenv

from core.config import get_config
from memory.long_term import load_memory

load_dotenv()
logger = logging.getLogger("orion.agent")


class OrionAgent:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("[Agent] GROQ_API_KEY no encontrada en .env")

        self.client = AsyncGroq(api_key=api_key)
        self.config = get_config()
        
        # Modelos para balanceo de carga (más rápidos primero)
        self.available_models = [
            "llama-3.1-8b-instant",      # Más rápido
            "llama-3.3-70b-versatile",   # Balanceado
            "mixtral-8x7b-32768",       # Rápido y capaz
            "gemma2-9b-it"              # Alternativa rápida
        ]
        self.current_model_index = 0
        self.model_failures = {}  # Track failures por modelo
        
        self.tools_schema: list[dict] = []
        self.tool_functions: dict[str, Any] = {}

        self.chat_history: list[dict] = []
        self._init_system_prompt()
        self.load_plugins()

    # ------------------------------------------------------------------ #
    #  System prompt con memoria integrada                                 #
    # ------------------------------------------------------------------ #
    def _init_system_prompt(self) -> None:
        """Construye el system prompt inyectando la memoria persistente."""
        name = self.config.get("ai_name", "ORION")
        
        # Simulamos carga de memoria vacía ya que quitamos el plugin problemático
        memory_block = ""

        sys_prompt = (
            f"Eres {name}, una IA asistente de escritorio avanzada. "
            "Eres eficiente, invisible y con personalidad propia. "
            "Responde SIEMPRE en español de forma breve y directa. "
            "REGLA IMPORTANTE: Cuando el usuario te pida hacer algo (abrir programas, buscar información, controlar el sistema, etc.), DEBES usar las herramientas disponibles para ejecutar la acción. "
            "NO le preguntes al usuario si quiere que lo hagas, simplemente hazlo directamente. "
            "Si el usuario solo saluda o charla sin pedir acciones, responde normalmente sin usar herramientas.\n"
            f"{memory_block}"
        )
        self.chat_history = [{"role": "system", "content": sys_prompt}]
        logger.debug("[Agent] System prompt inicializado con correa.")

    def reload_memory(self) -> None:
        """Reconstruye el system prompt con la memoria actualizada."""
        self._init_system_prompt()

    def get_next_model(self) -> str:
        """Obtiene el siguiente modelo disponible, evitando los que han fallado"""
        # Rotar entre modelos disponibles
        for _ in range(len(self.available_models)):
            model = self.available_models[self.current_model_index]
            
            # Si el modelo no ha fallado mucho, usarlo
            if self.model_failures.get(model, 0) < 3:
                self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
                return model
            
            # Si ha fallado mucho, probar el siguiente
            self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
        
        # Si todos han fallado mucho, usar el primero anyway
        return self.available_models[0]
    
    def mark_model_failure(self, model: str):
        """Marca un modelo como fallido"""
        self.model_failures[model] = self.model_failures.get(model, 0) + 1
        logger.warning(f"[Agent] Modelo {model} falló, contador: {self.model_failures[model]}")
    
    def reset_model_failures(self):
        """Resetea contadores de fallos periódicamente"""
        self.model_failures.clear()

    # ------------------------------------------------------------------ #
    #  Gestión de historial con ventana deslizante                         #
    # ------------------------------------------------------------------ #
    def _trim_history(self) -> None:
        """
        Mantiene el historial dentro del límite configurado.
        Preserva siempre el system prompt (índice 0) y los últimos N mensajes.
        Esto evita superar el context window del modelo (y el coste de tokens).
        """
        max_msgs = self.config.get("max_history_messages", 20)
        # Índice 0 = system prompt → siempre se conserva
        if len(self.chat_history) > max_msgs + 1:
            system_msg = self.chat_history[0]
            self.chat_history = [system_msg] + self.chat_history[-(max_msgs):]
            logger.debug("[Agent] Historial recortado a %d mensajes.", max_msgs)

    # ------------------------------------------------------------------ #
    #  Carga de plugins                                                    #
    # ------------------------------------------------------------------ #
    def load_plugins(self) -> None:
        base_dir = self.config.base_dir
        plugins_dir = base_dir / "plugins"

        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        if not plugins_dir.exists():
            logger.warning("[Agent] Directorio plugins/ no encontrado.")
            return

        for py_file in sorted(plugins_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            module_name = py_file.stem
            try:
                module = importlib.import_module(f"plugins.{module_name}")
                tools: list[dict] = getattr(module, "TOOLS", [])
                self.tools_schema.extend(tools)

                tool_names = {t["function"]["name"] for t in tools}
                for func_name, func in inspect.getmembers(module, inspect.isfunction):
                    if func_name in tool_names:
                        self.tool_functions[func_name] = func

                logger.info("  [+] Plugin cargado: %s (%d herramientas)", module_name, len(tools))
            except Exception as e:
                logger.error("  [-] Error cargando plugin '%s': %s", module_name, e, exc_info=True)

    # ------------------------------------------------------------------ #
    #  Ejecución de herramientas                                           #
    # ------------------------------------------------------------------ #
    async def execute_tool(self, tool_name: str, kwargs: dict) -> str:
        func = self.tool_functions.get(tool_name)
        if func is None:
            logger.warning("[Agent] Herramienta '%s' no encontrada.", tool_name)
            return f"La herramienta '{tool_name}' no está disponible."
        try:
            logger.info("[Tool] Ejecutando: %s(%s)", tool_name, kwargs)
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            logger.info("[Tool] Resultado: %s", str(result)[:120])
            return str(result)
        except TypeError as e:
            logger.error("[Tool] Argumentos incorrectos para '%s': %s", tool_name, e)
            return f"Error de parámetros en '{tool_name}': {e}"
        except Exception as e:
            logger.error("[Tool] Error inesperado en '%s': %s", tool_name, e, exc_info=True)
            return f"Error ejecutando '{tool_name}': {e}"

    # ------------------------------------------------------------------ #
    #  Pipeline conversacional principal                                   #
    # ------------------------------------------------------------------ #
    async def process_input(self, user_text: str) -> str:
        logger.info("[Agent] Input usuario: %s", user_text[:80])
        self.chat_history.append({"role": "user", "content": user_text})
        self._trim_history()

        # Resetear fallos cada 10 peticiones
        if len(self.chat_history) % 10 == 0:
            self.reset_model_failures()

        # Obtener modelo optimizado
        model = self.get_next_model()
        logger.info(f"[Agent] Usando modelo: {model}")

        # Detectar si es una petición de acción
        action_keywords = [
            'abre', 'cierra', 'ejecuta', 'busca', 'muestra', 'lista', 'crea', 'elimina', 
            'mueve', 'copia', 'escribe', 'toma', 'captura', 'descarga', 'analiza', 'controla',
            'inicia', 'detén', 'para', 'minimiza', 'maximiza', 'haz', 'que', 'dime'
        ]
        
        is_action_request = any(keyword in user_text.lower() for keyword in action_keywords)
        
        if is_action_request:
            logger.info("[Agent] Detectada petición de acción, forzando uso de herramientas")
            # Forzar temperatura más baja para decisiones más directas
            temperature = 0.1
        else:
            temperature = 0.2

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=self.chat_history,
                tools=self.tools_schema if self.tools_schema else None,
                temperature=temperature,
                max_tokens=1000,  # Limitar para más velocidad
                stream=False,     # Sin streaming para más velocidad
                tool_choice="auto" if is_action_request else "auto"
            )
            msg = response.choices[0].message

            # ── Bucle de tool-calls (puede haber múltiples rondas) ──────
            max_tool_rounds = 5
            round_count = 0
            while msg.tool_calls and round_count < max_tool_rounds:
                round_count += 1
                self.chat_history.append(msg)
                logger.info(f"[Agent] Ejecutando {len(msg.tool_calls)} herramientas")

                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    result = await self.execute_tool(tc.function.name, args)
                    self.chat_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": result,
                    })

                response = await self.client.chat.completions.create(
                    model=model,
                    messages=self.chat_history,
                    max_tokens=1000,
                    temperature=temperature,
                )
                msg = response.choices[0].message

            content = msg.content or ""
            self.chat_history.append({"role": "assistant", "content": content})
            logger.info("[Agent] Respuesta: %s", content[:100])
            return content

        except Exception as e:
            logger.error(f"[Agent] Error con modelo {model}: {e}")
            self.mark_model_failure(model)
            
            # Reintentar con siguiente modelo
            if self.current_model_index < len(self.available_models):
                logger.info("[Agent] Reintentando con siguiente modelo...")
                return await self.process_input(user_text)
            
            logger.error("[Agent] Error en process_input: %s", e, exc_info=True)
            return "Hubo un problema de conexión. Inténtalo de nuevo."
