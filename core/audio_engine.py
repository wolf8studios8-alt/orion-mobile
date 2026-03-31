from __future__ import annotations
import asyncio
import io
import logging
import threading
import wave
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot
from core.agent import OrionAgent
from core.config import get_config

# Importaciones condicionales
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("PyAudio no disponible - funcionalidad de audio desactivada")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("Edge TTS no disponible - síntesis de voz desactivada")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("Pygame no disponible - reproducción de audio desactivada")

logger = logging.getLogger("orion.audio")

class AudioEngine(QObject):
    speaking_started = Signal()
    speaking_stopped = Signal()
    listening_started = Signal()
    listening_stopped = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.config = get_config()
        self.agent = OrionAgent()
        
        if PYAUDIO_AVAILABLE:
            self.pya = pyaudio.PyAudio()
        else:
            self.pya = None
            
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
        else:
            logger.warning("Pygame no inicializado")
            
        self.is_running = True
        self._is_playing = False
        self.text_input_queue: asyncio.Queue[str] = asyncio.Queue()
        self.loop = asyncio.new_event_loop()

    async def listen_audio(self) -> None:
        if not PYAUDIO_AVAILABLE or not self.pya:
            logger.warning("Audio listening no disponible - PyAudio no instalado")
            await asyncio.sleep(1)  # Evitar bucle consumiendo CPU
            return
        
        try:
            stream = self.pya.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        except: return
        recording = False
        audio_frames = []
        threshold = self.config.get("mic_threshold", 150)

        while self.is_running:
            data = await asyncio.to_thread(stream.read, 1024, exception_on_overflow=False)
            if self._is_playing: continue
            
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(samples ** 2)))
            
            if rms > threshold:
                if not recording:
                    recording = True
                    self.listening_started.emit()
                audio_frames.append(data)
            elif recording:
                recording = False
                self.listening_stopped.emit()
                if len(audio_frames) > 10:
                    await self.transcribe_audio(b"".join(audio_frames))
                audio_frames = []
        stream.close()

    async def transcribe_audio(self, pcm: bytes) -> None:
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000); wf.writeframes(pcm)
        wav_io.seek(0)
        try:
            trans = await self.agent.client.audio.transcriptions.create(file=("audio.wav", wav_io.read()), model="whisper-large-v3-turbo")
            if trans.text: await self.text_input_queue.put(trans.text)
        except Exception as e: logger.error(f"STT Error: {e}")

    async def process_conversation(self) -> None:
        while self.is_running:
            user_text = await self.text_input_queue.get()
            resp = await self.agent.process_input(user_text)
            if resp: await self.tts(resp)
            self.text_input_queue.task_done()

    async def tts(self, text: str) -> None:
        if not EDGE_TTS_AVAILABLE:
            logger.warning("Síntesis de voz no disponible - Edge TTS no instalado")
            return
            
        self._is_playing = True
        self.speaking_started.emit()
        
        try:
            import uuid
            import os
            import glob
            
            # Generar nombre único para evitar conflictos de permisos
            unique_filename = f"orion_speech_{uuid.uuid4().hex[:8]}.mp3"
            comm = edge_tts.Communicate(text, "es-ES-AlvaroNeural")
            await comm.save(unique_filename)
            
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(unique_filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and self.is_running: 
                    await asyncio.sleep(0.1)
                
                # Limpiar archivo después de usarlo
                try:
                    os.remove(unique_filename)
                    logger.info(f"[Audio] Archivo temporal eliminado: {unique_filename}")
                except Exception as cleanup_error:
                    logger.warning(f"[Audio] Error limpiando archivo: {cleanup_error}")
            else:
                logger.warning("Reproducción de audio no disponible - Pygame no instalado")
                
        except Exception as e:
            logger.error(f"Error en TTS: {e}")
            
        self.speaking_stopped.emit()
        self._is_playing = False
        
        # Limpieza periódica de archivos viejos
        await self.cleanup_old_audio_files()

    async def cleanup_old_audio_files(self):
        """Limpia archivos de audio temporales viejos"""
        try:
            import glob
            import os
            import time
            
            # Buscar archivos orion_speech_*.mp3
            pattern = "orion_speech_*.mp3"
            files = glob.glob(pattern)
            
            # Eliminar archivos más viejos de 5 minutos
            current_time = time.time()
            for file in files:
                try:
                    file_age = current_time - os.path.getctime(file)
                    if file_age > 300:  # 5 minutos
                        os.remove(file)
                        logger.info(f"[Audio] Eliminado archivo viejo: {file}")
                except Exception as e:
                    logger.warning(f"[Audio] Error eliminando {file}: {e}")
        except Exception as e:
            logger.error(f"[Audio] Error en limpieza periódica: {e}")

    def start_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.gather(self.listen_audio(), self.process_conversation()))

    def stop(self):
        self.is_running = False
        if PYGAME_AVAILABLE:
            pygame.mixer.quit()
        if PYAUDIO_AVAILABLE and self.pya:
            self.pya.terminate()

    @Slot(str)
    def handle_user_text(self, text):
        asyncio.run_coroutine_threadsafe(self.text_input_queue.put(text), self.loop)