"""
UI Móvil para ORION - Estilo Google Assistant
Interfaz flotante minimalista con activación por voz
"""
import math
import random
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal, Slot, QPropertyAnimation, QPoint, QTimer, Qt
from PySide6.QtGui import QFont, QCursor, QIcon
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class OrionMobileWindow(QtWidgets.QWidget):
    text_submitted = Signal(str)
    voice_toggle_requested = Signal()
    
    def __init__(self):
        super().__init__()
        
        # --- Configuración Visual Móvil ---
        self.is_active = False  # Estado: activo/inactivo
        self.is_listening = False  # Estado: escuchando
        self.current_state = "sleeping"  # sleeping, listening, responding
        self.pulse = 0.0
        self.opacity = 0.1  # Comienza casi invisible
        
        # Colores estilo Google Assistant
        self.colors = {
            "sleeping": (QtGui.QColor(50, 50, 50, 200), QtGui.QColor(30, 30, 30, 150)),  # Azul oscuro
            "listening": (QtGui.QColor(0, 255, 150, 200), QtGui.QColor(0, 200, 100, 150)),  # Verde brillante
            "responding": (QtGui.QColor(100, 100, 255, 200), QtGui.QColor(50, 50, 200, 150)),  # Azul activo
        }
        
        # --- Configuración de Ventana Móvil ---
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint | 
            QtCore.Qt.Tool |
            QtCore.Qt.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        
        # Tamaño móvil (compacto)
        self.setFixedSize(300, 80)
        
        # Posición inicial (esquina inferior derecha)
        screen = QtGui.QGuiApplication.primaryScreen().geometry()
        self.move(
            screen.width() - 320,
            screen.height() - 120
        )
        
        # --- Efecto de sombra suave ---
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QtGui.QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # --- Layout móvil ---
        self.setup_mobile_layout()
        
        # --- Timers para animaciones ---
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_timer.start(50)
        
        # --- Timer para hotword detection (simulado) ---
        self.hotword_timer = QTimer(self)
        self.hotword_timer.timeout.connect(self._check_hotword)
        self.hotword_timer.start(100)
        
        # Estado inicial
        self.set_state("sleeping")
        
    def setup_mobile_layout(self):
        """Configura el layout estilo móvil"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        # --- Contenedor principal ---
        main_container = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # --- Ícono de ORION (círculo animado) ---
        self.icon_container = QtWidgets.QWidget()
        self.icon_container.setFixedSize(40, 40)
        self.icon_container.setStyleSheet("""
            QWidget {
                background: rgba(20, 20, 30, 180);
                border-radius: 20px;
                border: 2px solid rgba(100, 100, 255, 100);
            }
        """)
        
        # --- Barra de texto (solo cuando está activo) ---
        self.input_bar = QtWidgets.QLineEdit()
        self.input_bar.setPlaceholderText("Pregúntame a ORION...")
        self.input_bar.setFont(QFont("Segoe UI", 9))
        self.input_bar.setStyleSheet("""
            QLineEdit {
                background: rgba(10, 15, 30, 200);
                color: #ffffff;
                border: 1px solid rgba(100, 100, 255, 150);
                border-radius: 15px;
                padding: 8px 12px;
                selection-background-color: rgba(100, 100, 255, 100);
            }
            QLineEdit:focus {
                border: 1px solid rgba(100, 100, 255, 255);
                background: rgba(10, 15, 30, 220);
            }
        """)
        self.input_bar.returnPressed.connect(self._on_submit)
        self.input_bar.hide()  # Oculto inicialmente
        
        # --- Añadir al layout ---
        main_layout.addWidget(self.icon_container)
        main_layout.addWidget(self.input_bar)
        main_layout.addStretch()
        
        layout.addWidget(main_container)
        
    def _update_pulse(self):
        """Actualiza animación de pulso"""
        self.pulse += 0.1
        self.update()
        
    def _check_hotword(self):
        """Simula detección de hotword (para demostración)"""
        # En producción, esto usaría reconocimiento de voz real
        # Por ahora, simulamos con teclas o comandos
        pass
        
    def activate_orion(self):
        """Activa ORION (como decir 'Hey ORION')"""
        if not self.is_active:
            self.is_active = True
            self.set_state("listening")
            self.input_bar.show()
            self.animate_fade_in()
            logger.info("[Mobile] ORION activado")
            
    def deactivate_orion(self):
        """Desactiva ORION"""
        if self.is_active:
            self.is_active = False
            self.set_state("sleeping")
            self.input_bar.hide()
            self.animate_fade_out()
            logger.info("[Mobile] ORION desactivado")
            
    def animate_fade_in(self):
        """Animación de aparición suave"""
        self.opacity = 0.1
        for i in range(10):
            self.opacity = min(0.9, self.opacity + 0.08)
            self.setWindowOpacity(self.opacity)
            QtCore.QCoreApplication.processEvents()
            QtCore.QTimer.singleShot(30, lambda: None)
            
    def animate_fade_out(self):
        """Animación de desaparición suave"""
        for i in range(10):
            self.opacity = max(0.1, self.opacity - 0.08)
            self.setWindowOpacity(self.opacity)
            QtCore.QCoreApplication.processEvents()
            QtCore.QTimer.singleShot(30, lambda: None)
            
    def set_state(self, state):
        """Cambia el estado visual"""
        if state in self.colors:
            self.current_state = state
            self.update()
            
    def _on_submit(self):
        """Maneja envío de texto"""
        text = self.input_bar.text().strip()
        if text:
            self.text_submitted.emit(text)
            self.input_bar.clear()
            self.set_state("responding")
            
    def paintEvent(self, event):
        """Dibuja la interfaz móvil"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        if self.is_active:
            # --- Fondo principal (solo cuando está activo) ---
            c1, c2 = self.colors[self.current_state]
            
            # Gradiente principal
            gradient = QtGui.QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)
            painter.setBrush(gradient)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)
            
            # --- Ícono animado de ORION ---
            if self.current_state == "listening":
                # Efecto de ondas expansivas
                center = QtCore.QPoint(30, 30)
                for i in range(3):
                    radius = 15 + i * 8 + math.sin(self.pulse + i) * 3
                    alpha = 100 - i * 30
                    color = QtGui.QColor(0, 255, 150, alpha)
                    painter.setBrush(QtGui.QBrush(color))
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawEllipse(center, int(radius), int(radius))
                    
            elif self.current_state == "responding":
                # Efecto de rotación suave
                center = QtCore.QPoint(30, 30)
                radius = 18 + math.sin(self.pulse * 2) * 2
                painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 255, 200)))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(center, int(radius), int(radius))
                
        else:
            # --- Modo sleeping: solo un punto pequeño ---
            center = QtCore.QPoint(30, 30)
            radius = 5 + math.sin(self.pulse * 3) * 1
            painter.setBrush(QtGui.QBrush(QtGui.QColor(50, 50, 50, 150)))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(center, int(radius), int(radius))
            
    def mousePressEvent(self, event):
        """Click para activar/desactivar"""
        if event.button() == QtCore.Qt.LeftButton:
            if self.is_active:
                self.deactivate_orion()
            else:
                self.activate_orion()
                
    def mouseMoveEvent(self, event):
        """Permite mover la ventana"""
        if event.buttons() == QtCore.Qt.LeftButton and self.is_active:
            self.move(self.pos() + event.globalPos() - self.old_pos)
            self.old_pos = event.globalPos()
            
    def enterEvent(self, event):
        """Al entrar con el mouse, activar si está sleeping"""
        if not self.is_active:
            self.old_pos = event.globalPos()
            
    @Slot(str)
    def set_listening_state(self, is_listening):
        """Para integración con motor de audio"""
        self.is_listening = is_listening
        if is_listening:
            self.set_state("listening")
        else:
            self.set_state("responding")
