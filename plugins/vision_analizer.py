import cv2
import base64
import os
import logging
from groq import AsyncGroq

logger = logging.getLogger("orion.plugins.vision")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_surroundings",
            "description": "Toma una foto silenciosa con la cámara web del usuario para 'ver' el entorno. Úsalo si el usuario dice 'qué ves', 'mírame', o pregunta por algo físico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string", 
                        "description": "La instrucción para analizar la imagen (ej: '¿Cuántos dedos estoy mostrando?' o 'Describe mi estado de ánimo')."
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]

async def analyze_surroundings(prompt="Describe lo que ves en esta imagen de forma detallada pero conversacional."):
    logger.info("[Visión] Activando nervio óptico...")
    
    # cv2.CAP_DSHOW arranca la cámara mucho más rápido en Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # Descartar los primeros frames (suelen ser oscuros mientras la cámara ajusta la luz)
    for _ in range(5): cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        logger.error("[Visión] Error al acceder a la cámara.")
        return "Fallo en el nervio óptico: no pude acceder a la cámara web."
    
    # Codificar la imagen para enviarla a la API
    _, buffer = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    logger.info("[Visión] Fotograma capturado. Enviando al córtex visual (Groq Llama Vision)...")
    
    try:
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        response = await client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=250
        )
        descripcion = response.choices[0].message.content
        logger.info("[Visión] Análisis completado.")
        return f"Esto es lo que he visto: {descripcion}"
    except Exception as e:
        logger.error(f"[Visión] Error en Groq: {e}")
        return f"Pude abrir los ojos, pero mi lóbulo occipital falló al procesar la imagen: {e}"