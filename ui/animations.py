import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QPen

class AIAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "idle" 
        self.audio_volume = 0.0  
        self.base_pulse = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30) 

    @Slot()
    def set_idle(self): 
        self.state = "idle"
        self.audio_volume = 0.0
        
    @Slot()
    def set_listening(self): 
        self.state = "listening"
        
    @Slot()
    def set_speaking(self): 
        self.state = "speaking"

    @Slot(float)
    def update_volume(self, volume):
        self.audio_volume = (self.audio_volume * 0.7) + (volume * 0.3)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.transparent)
        
        center = self.rect().center()
        
        if self.state == "idle":
            core_color, aura_color = QColor(0, 255, 255, 180), QColor(138, 43, 226, 60)
            dynamic_radius = 40 + (math.sin(self.base_pulse) * 5) 
        elif self.state == "listening":
            core_color, aura_color = QColor(50, 255, 150, 200), QColor(0, 255, 255, 80)
            dynamic_radius = 40 + (self.audio_volume * 35) 
        elif self.state == "speaking":
            core_color, aura_color = QColor(255, 50, 255, 200), QColor(138, 43, 226, 100)
            dynamic_radius = 45 + (self.audio_volume * 45) 

        gradient_aura = QRadialGradient(center, dynamic_radius * 1.8)
        gradient_aura.setColorAt(0, aura_color)
        gradient_aura.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(gradient_aura))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, dynamic_radius * 1.8, dynamic_radius * 1.8)

        gradient_core = QRadialGradient(center, dynamic_radius * 0.8)
        gradient_core.setColorAt(0, QColor(255, 255, 255, 255)) 
        gradient_core.setColorAt(0.5, core_color)
        gradient_core.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(gradient_core))
        painter.drawEllipse(center, dynamic_radius, dynamic_radius)

        if self.state != "idle":
            pen = QPen(core_color)
            pen.setWidthF(2.0 + (self.audio_volume * 3))
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, dynamic_radius * 1.2, dynamic_radius * 1.2)

    def update_animation(self):
        self.base_pulse += 0.05
        if self.audio_volume > 0.01: self.audio_volume *= 0.90 
        self.update()
