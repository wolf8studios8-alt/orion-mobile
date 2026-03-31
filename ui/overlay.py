import math
import random
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal, Slot, QPropertyAnimation, QPoint, QTimer, Qt
from PySide6.QtGui import QFont, QCursor, QIcon
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class OrionFloatingWindow(QtWidgets.QWidget):
    text_submitted = Signal(str)
    voice_toggle_requested = Signal()

    def __init__(self):
        super().__init__()
        
        # --- Configuración Visual ---
        self.diameter = 80  # Ícono flotante
        self.bar_height = 40  # Altura de la barra de comandos
        self.current_state = "normal"
        self.pulse = 0.0
        self.is_expanded = False
        self.command_bar_visible = True  # Siempre visible
        self.is_minimized = False
        self.base_width = 280  # Ancho total base (ícono + barra + márgenes)
        self.base_height = 100  # Altura total base
        
        # Posición y movimiento
        self.old_pos = None
        self.dragging = False
        self.original_pos = None
        
        # Colores extraídos de tu imagen (Cian, Azul eléctrico, Púrpura)
        self.colors = {
            "normal": (QtGui.QColor(0, 255, 255, 120), QtGui.QColor(0, 100, 255, 80), QtGui.QColor(150, 0, 255, 40)),
            "escucha": (QtGui.QColor(0, 255, 150, 150), QtGui.QColor(0, 200, 255, 100), QtGui.QColor(0, 50, 200, 50)),
            "habla": (QtGui.QColor(255, 0, 255, 180), QtGui.QColor(100, 0, 255, 120), QtGui.QColor(50, 0, 150, 60))
        }

        # --- Lógica de Evasión ---
        self.original_pos = None
        self.is_evaded = False
        self.evade_timer = QTimer(self)
        self.evade_timer.setSingleShot(True)
        self.evade_timer.timeout.connect(self.start_evasion)
        
        self.return_timer = QTimer(self)
        self.return_timer.setSingleShot(True)
        self.return_timer.timeout.connect(self.start_return)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(600)
        self.anim.setEasingCurve(QtCore.QEasingCurve.InOutCubic)

        # --- Configuración de Ventana ---
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFixedSize(self.base_width, self.base_height)
        
        # Efecto de sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 255, 255, 100))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        # --- Layout principal ---
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Contenedor horizontal para ícono y barra
        main_container = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # --- Barra de comandos integrada ---
        self.input_bar = QtWidgets.QLineEdit()
        self.input_bar.setPlaceholderText("Escriba comando...")
        font = QFont("Segoe UI", 10)
        self.input_bar.setFont(font)
        self.input_bar.setFixedWidth(180)
        self.input_bar.setStyleSheet("""
            QLineEdit {
                background: rgba(10, 15, 30, 240);
                color: #00ffff;
                border: 2px solid rgba(0, 255, 255, 150);
                border-radius: 12px;
                padding: 8px 12px;
                selection-background-color: rgba(0, 255, 255, 100);
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 255, 255, 255);
                background: rgba(10, 15, 30, 255);
            }
        """)
        self.input_bar.returnPressed.connect(self._on_submit)
        
        # Añadir widgets al layout
        main_layout.addWidget(self.input_bar)
        layout.addWidget(main_container)

        # Timer de animación fluida
        self.energy_timer = QTimer(self)
        self.energy_timer.timeout.connect(self._tick)
        self.energy_timer.start(30)

    def _tick(self):
        self.pulse += 0.05
        self.update()

    def _on_submit(self):
        if self.input_bar.text():
            self.text_submitted.emit(self.input_bar.text())
            self.input_bar.clear()

    # --- Interacciones del ícono flotante ---
    def enterEvent(self, event):
        self.return_timer.stop()
        if not self.is_evaded: 
            self.evade_timer.start(1500)
        # Expandir ligeramente al pasar el mouse
        self.expand_animation()

    def leaveEvent(self, event):
        self.evade_timer.stop()
        if self.is_evaded: 
            self.return_timer.start(3000)
        # Contraer al salir
        self.contract_animation()
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # Minimizar/expandir al hacer click
            self.toggle_minimize()
        elif event.button() == QtCore.Qt.RightButton:
            self.old_pos = event.globalPos()
            self.dragging = True
    
    def mouseDoubleClickEvent(self, event):
        # Doble click para activar/desactivar escucha de voz
        if event.button() == QtCore.Qt.LeftButton:
            self.toggle_voice_listening()
    
    def expand_animation(self):
        """Expande el ícono visualmente sin cambiar tamaño de ventana"""
        self.is_expanded = True
        # El tamaño de ventana no cambia, solo el estado visual
    
    def contract_animation(self):
        """Contráe el ícono a su tamaño base"""
        self.is_expanded = False
        # No cambiamos el tamaño de la ventana, solo el estado
    
    def toggle_minimize(self):
        """Minimiza o expandir la ventana"""
        if self.is_minimized:
            # Expandir a tamaño completo
            self.is_minimized = False
            self.setFixedSize(self.base_width, self.base_height)
            self.input_bar.show()
        else:
            # Minimizar a solo ícono
            self.is_minimized = True
            self.setFixedSize(self.diameter + 20, self.diameter + 20)
            self.input_bar.hide()
    
    def toggle_voice_listening(self):
        # Emitir señal para activar escucha de voz
        self.voice_toggle_requested.emit()

    def start_evasion(self):
        if not self.original_pos: self.original_pos = self.pos()
        self.is_evaded = True
        # Se mueve a una posición alejada (ej: 150px de diferencia)
        target = self.pos() + QPoint(150, 100)
        self.anim.setEndValue(target)
        self.anim.start()

    def start_return(self):
        if self.original_pos:
            self.is_evaded = False
            self.anim.setEndValue(self.original_pos)
            self.anim.start()

    @Slot(str)
    def set_state(self, state):
        if state in self.colors: self.current_state = state

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Solo dibujar el ícono si no está minimizado
        if not self.is_minimized:
            # Centro de la esfera (ajustado para el layout)
            if self.command_bar_visible:
                cx = 40  # Posición fija para el ícono
                cy = 40  # Posición fija para el ícono
            else:
                cx = self.width() // 2
                cy = self.height() // 2
            
            center = QtCore.QPoint(cx, cy)
            radius = self.diameter // 2
            
            c1, c2, c3 = self.colors[self.current_state]

            # CAPA 1: Brillo Exterior (Glow suave)
            outer_grad = QtGui.QRadialGradient(center, radius)
            outer_grad.setColorAt(0, c2)
            outer_grad.setColorAt(1, QtGui.QColor(0,0,0,0))
            painter.setBrush(outer_grad)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

            # CAPA 2: Energía Fluida (3 núcleos moviéndose)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Plus)
            
            for i in range(3):
                # Movimiento orbital de los núcleos de luz
                offset_x = math.cos(self.pulse + i * 2) * (radius * 0.3)
                offset_y = math.sin(self.pulse * 0.8 + i * 2) * (radius * 0.3)
                nucleus_pos = center + QPoint(int(offset_x), int(offset_y))
                
                # Tamaño cambiante del núcleo
                n_radius = radius * (0.5 + math.sin(self.pulse + i) * 0.1)
                
                n_grad = QtGui.QRadialGradient(nucleus_pos, n_radius)
                n_grad.setColorAt(0, c1)
                n_grad.setColorAt(1, QtGui.QColor(0,0,0,0))
                
                painter.setBrush(n_grad)
                painter.drawEllipse(nucleus_pos, int(n_radius), int(n_radius))

            # CAPA 3: Reflejo de cristal superior
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            glass_grad = QtGui.QLinearGradient(cx, cy - radius, cx, cy)
            glass_grad.setColorAt(0, QtGui.QColor(255, 255, 255, 30))
            glass_grad.setColorAt(1, QtGui.QColor(255, 255, 255, 0))
            painter.setBrush(glass_grad)
            painter.drawEllipse(center, int(radius*0.9), int(radius*0.8))

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == QtCore.Qt.RightButton:
            delta = event.globalPos() - self.old_pos
            new_pos = self.pos() + delta
            
            # Mantener dentro de la pantalla
            screen = QtGui.QGuiApplication.primaryScreen().geometry()
            new_x = max(0, min(new_pos.x(), screen.width() - self.width()))
            new_y = max(0, min(new_pos.y(), screen.height() - self.height()))
            
            self.move(new_x, new_y)
            self.old_pos = event.globalPos()
            self.original_pos = self.pos()
            
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.dragging = False