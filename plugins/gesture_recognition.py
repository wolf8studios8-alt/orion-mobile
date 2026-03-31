"""
Plugin de reconocimiento de gestos para ORION
Control por gestos de mano y cámara web
"""
import cv2
import numpy as np
import logging
import mediapipe as mp
from typing import Dict, Any

logger = logging.getLogger("orion.plugins.gesture")

# Inicializar MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Configuración
GESTURES = {
    "pulg_arriba": "scroll_up",
    "pulg_abajo": "scroll_down", 
    "paz": "click_izquierdo",
    "ok": "click_derecho",
    "punto": "minimizar_ventana",
    "victoria": "maximizar_ventana"
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_gesture_control",
            "description": "Inicia el control por gestos con la cámara web. Úsalo cuando el usuario pida control por gestos.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_gesture_control",
            "description": "Detiene el control por gestos. Úsalo cuando el usuario pida detener el reconocimiento.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

# Variables globales
gesture_active = False
camera = None

def start_gesture_control() -> str:
    """Inicia el reconocimiento de gestos"""
    global gesture_active, camera
    
    try:
        if not cv2_available():
            return "OpenCV no disponible para reconocimiento de gestos."
            
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            return "No se pudo acceder a la cámara web."
            
        gesture_active = True
        logger.info("[Gestos] Iniciando control por gestos...")
        
        # Iniciar en hilo separado para no bloquear
        import threading
        thread = threading.Thread(target=_gesture_loop, daemon=True)
        thread.start()
        
        return "Control por gestos activado. Muestra tu mano a la cámara para controlar."
        
    except Exception as e:
        logger.error(f"[Gestos] Error iniciando: {e}")
        return f"Error iniciando control por gestos: {e}"

def stop_gesture_control() -> str:
    """Detiene el reconocimiento de gestos"""
    global gesture_active, camera
    
    gesture_active = False
    if camera:
        camera.release()
        camera = None
        
    cv2.destroyAllWindows()
    logger.info("[Gestos] Control por gestos detenido")
    return "Control por gestos detenido."

def _gesture_loop():
    """Bucle principal de reconocimiento de gestos"""
    global gesture_active, camera
    
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:
        
        while gesture_active and camera:
            ret, frame = camera.read()
            if not ret:
                break
                
            # Voltear imagen horizontalmente
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Procesar con MediaPipe
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Dibujar puntos de la mano
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Detectar gesto
                    gesture = _detect_gesture(hand_landmarks)
                    if gesture:
                        logger.info(f"[Gestos] Gesto detectado: {gesture}")
                        _execute_gesture_action(gesture)
            
            # Mostrar instrucciones
            cv2.putText(frame, "Control por Gestos - ORION", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Pulsa ESC para salir", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imshow("ORION - Control por Gestos", frame)
            
            # Salir con ESC
            if cv2.waitKey(5) & 0xFF == 27:
                break

def _detect_gesture(landmarks) -> str:
    """Detecta gestos básicos"""
    try:
        # Obtener puntos clave
        thumb_tip = landmarks.landmark[4]
        thumb_ip = landmarks.landmark[2]
        index_tip = landmarks.landmark[8]
        middle_tip = landmarks.landmark[12]
        ring_tip = landmarks.landmark[16]
        pinky_tip = landmarks.landmark[20]
        
        # Gesto: Pulgar arriba/abajo
        if thumb_tip.y < thumb_ip.y:
            return "pulg_arriba"
        elif thumb_tip.y > thumb_ip.y + 0.1:
            return "pulg_abajo"
            
        # Gesto: Paz (mano abierta)
        if (thumb_tip.y < landmarks.landmark[0].y and 
            index_tip.y > landmarks.landmark[6].y and
            middle_tip.y > landmarks.landmark[10].y and
            ring_tip.y > landmarks.landmark[14].y and
            pinky_tip.y > landmarks.landmark[18].y):
            return "paz"
            
        # Gesto: OK
        if (abs(thumb_tip.x - index_tip.x) < 0.05 and
            abs(thumb_tip.y - index_tip.y) < 0.05):
            return "ok"
            
        # Gesto: Punto (índice)
        if (index_tip.y < landmarks.landmark[6].y and
            thumb_tip.y > landmarks.landmark[2].y):
            return "punto"
            
        # Gesto: Victoria (V)
        if (index_tip.y < landmarks.landmark[6].y and
            middle_tip.y > landmarks.landmark[10].y and
            ring_tip.y > landmarks.landmark[14].y and
            pinky_tip.y > landmarks.landmark[18].y):
            return "victoria"
            
    except Exception as e:
        logger.error(f"[Gestos] Error detectando gesto: {e}")
        
    return None

def _execute_gesture_action(gesture: str):
    """Ejecuta acción según gesto detectado"""
    try:
        import pyautogui
        import time
        
        action = GESTURES.get(gesture)
        
        if action == "scroll_up":
            pyautogui.scroll(3)
        elif action == "scroll_down":
            pyautogui.scroll(-3)
        elif action == "click_izquierdo":
            pyautogui.click(button='left')
        elif action == "click_derecho":
            pyautogui.click(button='right')
        elif action == "minimizar_ventana":
            pyautogui.hotkey('win', 'down')
        elif action == "maximizar_ventana":
            pyautogui.hotkey('win', 'up')
            
        logger.info(f"[Gestos] Acción ejecutada: {action}")
        
    except Exception as e:
        logger.error(f"[Gestos] Error ejecutando acción: {e}")

def cv2_available() -> bool:
    """Verifica si OpenCV está disponible"""
    try:
        import cv2
        return True
    except ImportError:
        return False
