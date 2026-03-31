import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("orion.plugins.web")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": "Busca información en Internet en tiempo real y devuelve los títulos y extractos. Úsalo para noticias, clima actual o datos que no sabes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término a buscar en el navegador."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_website",
            "description": "Lee el texto principal de una página web específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "La URL exacta a leer (https://...)."}
                },
                "required": ["url"]
            }
        }
    }
]

async def search_internet(query: str) -> str:
    logger.info(f"[Web] Ejecutando escaneo web para: '{query}'")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    url = f"https://html.duckduckgo.com/html/?q={query}"
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extraer los 3 primeros resultados limpios
        results = []
        for a in soup.find_all('a', class_='result__snippet', limit=3):
            results.append(a.text.strip())
            
        if not results:
            return "El motor de búsqueda no devolvió resultados útiles."
            
        return "Esto es lo que encontré en la red: " + " | ".join(results)
    except Exception as e:
        logger.error(f"[Web] Error de red: {e}")
        return f"Mi conexión a la red de búsqueda falló: {e}"

async def read_website(url: str) -> str:
    logger.info(f"[Web] Extrayendo datos de la URL: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Solo extraemos los párrafos para ignorar menús y scripts
        paragraphs = soup.find_all('p')
        text = " ".join([p.text for p in paragraphs])
        
        # Limitamos a 2500 caracteres para no ahogar la memoria a corto plazo
        limite = text[:2500] + ("..." if len(text) > 2500 else "")
        return f"Contenido de la web: {limite}"
    except Exception as e:
        return f"El firewall o el servidor me impidieron leer la página: {e}"