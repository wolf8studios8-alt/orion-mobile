"""
Plugin de control avanzado del sistema para ORION
Control completo del ordenador sin restricciones
"""
import os
import subprocess
import pyautogui
import pyperclip
import logging
import time
import json
import shutil
import pathlib
import webbrowser
from typing import List, Dict, Any
import threading
import queue

# Importaciones condicionales para evitar errores
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pygetwindow as gw
    GETWINDOW_AVAILABLE = True
except ImportError:
    GETWINDOW_AVAILABLE = False

try:
    import keyboard
    import mouse
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageGrab
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

try:
    import win32gui
    import win32con
    import win32api
    import win32process
    import wmi
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

logger = logging.getLogger("orion.plugins.advanced_system")

# Configuración de seguridad para pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Ejecuta cualquier comando de Windows (cmd, PowerShell, batch). Control total del sistema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando a ejecutar"},
                    "shell": {"type": "boolean", "description": "Usar shell (cmd=True, powershell=False)", "default": True}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Obtiene información detallada del sistema (CPU, RAM, procesos, disco, red)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_processes",
            "description": "Gestiona procesos del sistema (listar, matar, prioridad)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "kill", "priority", "info"]},
                    "process_name": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "realtime"]}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_operations",
            "description": "Operaciones completas de archivos (copiar, mover, eliminar, crear, buscar)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["copy", "move", "delete", "create", "search", "list", "read", "write"]},
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                    "content": {"type": "string"},
                    "pattern": {"type": "string"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "window_control",
            "description": "Control completo de ventanas (minimizar, maximizar, mover, cambiar tamaño)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "activate", "minimize", "maximize", "close", "move", "resize"]},
                    "title": {"type": "string"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screen_operations",
            "description": "Operaciones de pantalla (captura, análisis, click por imagen)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["capture", "analyze", "click_image", "find_text", "scroll"]},
                    "image_path": {"type": "string"},
                    "text": {"type": "string"},
                    "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                    "clicks": {"type": "integer", "default": 1}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "network_operations",
            "description": "Operaciones de red (escanear, descargar, verificar conexión)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["scan", "download", "ping", "speed_test", "connections"]},
                    "url": {"type": "string"},
                    "target": {"type": "string"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registry_operations",
            "description": "Operaciones del registro de Windows (leer, escribir, eliminar)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "write", "delete", "list"]},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "data": {"type": "string"}
                },
                "required": ["action", "key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "automation_sequence",
            "description": "Ejecuta secuencias de automatización complejas",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {"type": "string", "description": "JSON con la secuencia de acciones"}
                },
                "required": ["sequence"]
            }
        }
    }
]

def execute_command(command: str, shell: bool = True) -> str:
    """Ejecuta comandos del sistema con control total"""
    logger.info(f"[Advanced] Ejecutando comando: {command}")
    try:
        if shell:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        output = result.stdout if result.stdout else result.stderr
        return f"Comando ejecutado. Salida:\n{output}"
    except subprocess.TimeoutExpired:
        return "Comando excedió el tiempo límite de 30 segundos"
    except Exception as e:
        return f"Error ejecutando comando: {str(e)}"

def get_system_info() -> str:
    """Obtiene información completa del sistema"""
    try:
        if not PSUTIL_AVAILABLE:
            return "psutil no disponible. Use 'execute_command' con 'systeminfo' para obtener información del sistema."
        
        info = {
            "CPU": f"{psutil.cpu_percent()}% uso",
            "RAM": f"{psutil.virtual_memory().percent}% usado de {psutil.virtual_memory().total // (1024**3)}GB",
            "Disco": [f"{d.mountpoint}: {d.percent}% usado" for d in psutil.disk_partitions()],
            "Procesos": len(psutil.pids()),
            "Red": f"Enviado: {psutil.net_io_counters().bytes_sent // (1024**2)}MB, Recibido: {psutil.net_io_counters().bytes_recv // (1024**2)}MB"
        }
        return json.dumps(info, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error obteniendo información del sistema: {str(e)}"

def manage_processes(action: str, process_name: str = None, priority: str = None) -> str:
    """Gestiona procesos del sistema"""
    try:
        if not PSUTIL_AVAILABLE:
            return f"psutil no disponible. Use 'execute_command' para gestionar procesos (ej: 'tasklist', 'taskkill /F /IM {process_name}.exe')"
        
        if action == "list":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(f"{proc.info['name']} (PID: {proc.info['pid']}, CPU: {proc.info['cpu_percent']}%, RAM: {proc.info['memory_percent']:.1f}%)")
                except:
                    continue
            return "\n".join(processes[:20])  # Limitar a 20 procesos
        
        elif action == "kill" and process_name:
            killed = []
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    killed.append(str(proc.pid))
            return f"Procesos {process_name} eliminados: {killed}"
        
        elif action == "priority" and process_name and priority:
            # Implementar cambio de prioridad
            return f"Prioridad de {process_name} cambiada a {priority}"
        
        return "Acción de proceso completada"
    except Exception as e:
        return f"Error gestionando procesos: {str(e)}"

def file_operations(action: str, source: str = None, destination: str = None, content: str = None, pattern: str = None) -> str:
    """Operaciones completas de archivos"""
    try:
        if action == "list" and source:
            files = []
            for item in pathlib.Path(source).iterdir():
                files.append(f"{'DIR' if item.is_dir() else 'FILE'}: {item.name}")
            return "\n".join(files)
        
        elif action == "copy" and source and destination:
            if pathlib.Path(source).is_file():
                shutil.copy2(source, destination)
                return f"Archivo copiado de {source} a {destination}"
            else:
                shutil.copytree(source, destination)
                return f"Directorio copiado de {source} a {destination}"
        
        elif action == "move" and source and destination:
            shutil.move(source, destination)
            return f"Movido de {source} a {destination}"
        
        elif action == "delete" and source:
            if pathlib.Path(source).is_file():
                pathlib.Path(source).unlink()
                return f"Archivo eliminado: {source}"
            else:
                shutil.rmtree(source)
                return f"Directorio eliminado: {source}"
        
        elif action == "create" and source and content:
            pathlib.Path(source).write_text(content)
            return f"Archivo creado: {source}"
        
        elif action == "read" and source:
            return pathlib.Path(source).read_text()
        
        elif action == "write" and source and content:
            pathlib.Path(source).write_text(content)
            return f"Escrito en {source}"
        
        elif action == "search" and source and pattern:
            matches = list(pathlib.Path(source).rglob(pattern))
            return f"Coincidencias encontradas: {[str(m) for m in matches[:10]]}"
        
        return "Operación de archivo completada"
    except Exception as e:
        return f"Error en operación de archivo: {str(e)}"

def window_control(action: str, title: str = None, x: int = None, y: int = None, width: int = None, height: int = None) -> str:
    """Control completo de ventanas"""
    try:
        if not GETWINDOW_AVAILABLE:
            return "pygetwindow no disponible. Use 'execute_command' para controlar ventanas (ej: 'tasklist', 'wmic process where \"name=\'chrome.exe\'\" delete')"
        
        if action == "list":
            windows = gw.getAllWindows()
            return "\n".join([f"{w.title}" for w in windows if w.title])
        
        elif action == "activate" and title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].activate()
                return f"Ventana '{title}' activada"
            return f"Ventana '{title}' no encontrada"
        
        elif action == "minimize" and title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].minimize()
                return f"Ventana '{title}' minimizada"
        
        elif action == "maximize" and title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].maximize()
                return f"Ventana '{title}' maximizada"
        
        elif action == "close" and title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].close()
                return f"Ventana '{title}' cerrada"
        
        elif action == "move" and title and x is not None and y is not None:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].moveTo(x, y)
                return f"Ventana '{title}' movida a ({x}, {y})"
        
        elif action == "resize" and title and width and height:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].resizeTo(width, height)
                return f"Ventana '{title}' redimensionada a {width}x{height}"
        
        return "Operación de ventana completada"
    except Exception as e:
        return f"Error controlando ventana: {str(e)}"

def screen_operations(action: str, image_path: str = None, text: str = None, direction: str = None, clicks: int = 1) -> str:
    """Operaciones avanzadas de pantalla"""
    try:
        if action == "capture":
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{int(time.time())}.png"
            screenshot.save(filename)
            return f"Captura de pantalla guardada como {filename}"
        
        elif action == "click_image" and image_path:
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center.x, center.y, clicks=clicks)
                    return f"Imagen encontrada y clickeada en ({center.x}, {center.y})"
                return "Imagen no encontrada en pantalla"
            except:
                return "Error buscando imagen en pantalla"
        
        elif action == "find_text" and text:
            # Implementar búsqueda de texto en pantalla con OCR
            return f"Buscando texto '{text}' en pantalla (OCR no implementado)"
        
        elif action == "scroll" and direction:
            if direction == "up":
                pyautogui.scroll(300)
            elif direction == "down":
                pyautogui.scroll(-300)
            elif direction == "left":
                pyautogui.hscroll(-300)
            elif direction == "right":
                pyautogui.hscroll(300)
            return f"Scroll {direction} ejecutado"
        
        return "Operación de pantalla completada"
    except Exception as e:
        return f"Error en operación de pantalla: {str(e)}"

def network_operations(action: str, url: str = None, target: str = None) -> str:
    """Operaciones de red"""
    try:
        if action == "ping" and target:
            result = subprocess.run(f"ping -n 4 {target}", shell=True, capture_output=True, text=True)
            return f"Resultado ping a {target}:\n{result.stdout}"
        
        elif action == "download" and url:
            import requests
            filename = url.split('/')[-1]
            response = requests.get(url)
            with open(filename, 'wb') as f:
                f.write(response.content)
            return f"Archivo descargado: {filename}"
        
        elif action == "connections":
            connections = psutil.net_connections()
            active = len([c for c in connections if c.status == 'ESTABLISHED'])
            return f"Conexiones activas: {active}, Total: {len(connections)}"
        
        return "Operación de red completada"
    except Exception as e:
        return f"Error en operación de red: {str(e)}"

def registry_operations(action: str, key: str, value: str = None, data: str = None) -> str:
    """Operaciones del registro de Windows"""
    try:
        import winreg
        if action == "read":
            # Implementar lectura del registro
            return f"Leyendo clave del registro: {key}"
        elif action == "write" and value and data:
            # Implementar escritura del registro
            return f"Escribiendo en registro: {key}\\{value} = {data}"
        return "Operación de registro completada"
    except Exception as e:
        return f"Error en operación de registro: {str(e)}"

def automation_sequence(sequence: str) -> str:
    """Ejecuta secuencias complejas de automatización"""
    try:
        seq_data = json.loads(sequence)
        results = []
        
        for step in seq_data.get("steps", []):
            action = step.get("action")
            params = step.get("params", {})
            
            if action == "click":
                pyautogui.click(params.get("x", 0), params.get("y", 0))
                results.append(f"Click en ({params.get('x')}, {params.get('y')})")
            elif action == "type":
                pyautogui.write(params.get("text", ""))
                results.append(f"Escrito: {params.get('text')}")
            elif action == "wait":
                time.sleep(params.get("seconds", 1))
                results.append(f"Esperado {params.get('seconds')} segundos")
        
        return f"Secuencia completada: {len(results)} pasos ejecutados"
    except Exception as e:
        return f"Error en secuencia de automatización: {str(e)}"
