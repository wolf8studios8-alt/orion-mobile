import os
import subprocess
import logging
import time

# Importaciones condicionales
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

logger = logging.getLogger("orion.plugins.system")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Abre una aplicación o programa en Windows. Úsalo cuando el usuario pida abrir algo.",
            "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Cierra un programa activo en Windows. Úsalo cuando el usuario pida cerrar algo.",
            "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Escribe texto en la pantalla actual. Úsalo cuando el usuario pida escribir algo.",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Pulsa una tecla especial. Úsalo cuando el usuario pida pulsar teclas.",
            "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_clipboard",
            "description": "Lee el texto del portapapeles. Úsalo cuando el usuario pida ver qué hay copiado.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_system",
            "description": "Apaga y cierra completamente a ORION. Úsalo solo si el usuario lo pide explícitamente.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

def open_application(name: str) -> str:
    logger.info("[Sistema] Abriendo proceso: %s", name)
    try:
        subprocess.Popen(f"start {name}", shell=True)
        # IMPORTANTE: Pausamos 2 segundos para dar tiempo a que Windows abra la ventana
        time.sleep(2) 
        return f"Ejecutando {name}. La ventana debería estar abierta y en foco ahora."
    except Exception as e:
        logger.error("[Sistema] Error al abrir %s: %s", name, e)
        return f"Error al abrir {name}."

def close_application(name: str) -> str:
    logger.info("[Sistema] Matando proceso: %s", name)
    exit_code = os.system(f"taskkill /F /IM {name}.exe /T")
    if exit_code == 0: 
        return f"Proceso {name} finalizado con fuerza letal."
    return f"No encontré {name} en ejecución."

def type_text(text: str) -> str:
    logger.info("[Sistema] Simulando teclado para escribir: %s...", text[:20])
    if not PYAUTOGUI_AVAILABLE:
        return "pyautogui no disponible. Use 'execute_command' para automatización de teclado."
    try:
        pyautogui.write(text, interval=0.03)
        return f"Texto escrito. Si necesitas confirmar, recuerda usar la herramienta press_key con 'enter'."
    except Exception as e:
        logger.error("[Sistema] Fallo teclado: %s", e)
        return "Fallo en la emulación de teclado."

def press_key(key: str) -> str:
    logger.info(f"[Sistema] Pulsando tecla: {key}")
    if not PYAUTOGUI_AVAILABLE:
        return "pyautogui no disponible. Use 'execute_command' para simulación de teclado."
    try:
        # Limpiar la entrada de la IA por si manda "Enter" con mayúscula
        key = key.lower().strip()
        pyautogui.press(key)
        return f"Tecla '{key}' pulsada con éxito."
    except Exception as e:
        return f"No se pudo pulsar la tecla {key}: {e}"

def read_clipboard() -> str:
    logger.info("[Sistema] Leyendo portapapeles...")
    if not PYPERCLIP_AVAILABLE:
        return "pyperclip no disponible. Use 'execute_command' con 'clip' para acceder al portapapeles."
    try:
        content = pyperclip.paste()
        if not content: return "El portapapeles está vacío."
        return f"El usuario tiene copiado esto: {content}"
    except Exception as e:
        logger.error("[Sistema] Fallo portapapeles: %s", e)
        return "Error leyendo memoria del portapapeles."

def shutdown_system() -> str:
    logger.info("[Sistema] Secuencia de apagado iniciada por el usuario.")
    # Usamos os._exit(0) para matar el proceso de Python instantáneamente 
    # y evitar que el loop de eventos se quede colgado.
    os._exit(0)
    return "Apagando..."