"""
ORION Mobile - Versión Android con Kivy
Interfaz táctil móvil con activación por voz
"""
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse, Line
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
import requests
import threading
import json

# Simular funciones de ORION (en producción usar las reales)
def orion_process_command(command):
    """Procesa comandos de ORION"""
    responses = {
        "hola": "¡Hola! Soy ORION, tu asistente móvil.",
        "qué tiempo hace": "Lo siento, no tengo acceso a internet en esta versión móvil.",
        "abre cámara": "Abriendo cámara...",
        "enciende luces": "Las luces han sido encendidas.",
        "reproduce música": "Reproduciendo tu música favorita.",
        "default": f"Entendido: '{command}'. ¿En qué puedo ayudarte?"
    }
    
    return responses.get(command.lower(), responses["default"])

class OrionMobileApp(App):
    def build(self):
        # Configurar ventana móvil
        Window.clearcolor = (0.1, 0.1, 0.2, 1)  # Fondo oscuro
        Window.title = "ORION Mobile"
        
        # Layout principal flotante
        root = FloatLayout()
        
        # --- Contenedor principal ---
        main_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.9, 0.4),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=20,
            spacing=10
        )
        
        # --- Canvas para el círculo animado ---
        self.status_widget = FloatLayout(size_hint=(1, 0.3))
        
        # --- Barra de entrada ---
        self.input_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            spacing=10,
            opacity=0  # Oculto inicialmente
        )
        
        self.text_input = TextInput(
            hint_text='Pregúntame a ORION...',
            size_hint=(0.8, None),
            background_color=(0.1, 0.1, 0.2, 0.8),
            foreground_color=(1, 1, 1, 1),
            border_color=(0.2, 0.6, 1.0, 1),
            border_radius=15,
            padding=(15, 10),
            multiline=False
        )
        
        self.send_button = Button(
            text='Enviar',
            size_hint=(0.2, None),
            background_color=(0.2, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
            border_radius=15
        )
        self.send_button.bind(on_press=self.send_command)
        
        self.input_container.add_widget(self.text_input)
        self.input_container.add_widget(self.send_button)
        
        # --- Botón de activación (cuando está inactivo) ---
        self.activate_button = Button(
            text='🎤 ORION',
            size_hint=(0.8, 0.15),
            background_color=(0.1, 0.1, 0.2, 0.9),
            color=(1, 1, 1, 0.7),
            border_radius=20,
            font_size='20sp'
        )
        self.activate_button.bind(on_press=self.activate_orion)
        
        # --- Mensaje de estado ---
        self.status_label = Label(
            text='Toca para activar ORION',
            size_hint=(1, None),
            color=(1, 1, 1, 0.7),
            font_size='14sp',
            halign='center'
        )
        
        # Ensamblar interfaz
        main_container.add_widget(self.status_widget)
        main_container.add_widget(self.status_label)
        main_container.add_widget(self.input_container)
        main_container.add_widget(self.activate_button)
        
        root.add_widget(main_container)
        
        # Estado inicial
        self.is_active = False
        self.animation_pulse = 0
        
        # Animación inicial
        Clock.schedule_interval(self.update_animation, 0.1)
        
        return root
    
    def update_animation(self, dt):
        """Actualiza animación del círculo"""
        if self.is_active:
            self.animation_pulse += 0.1
            # Limpiar canvas y redibujar
            self.status_widget.canvas.clear()
            with self.status_widget.canvas:
                Color(0.2, 0.6, 1.0, 0.8 + 0.2 * abs(self.animation_pulse % (2 * 3.14159)))
                # Círculo principal con tamaño variable
                size = 50 + 5 * abs(self.animation_pulse % (2 * 3.14159))
                Ellipse(pos=(self.status_widget.width/2 - size/2, self.status_widget.height/2 - size/2), 
                       size=(size, size))
                Color(1, 1, 1, 0.3)
                Line(ellipse=(self.status_widget.width/2 - 25, self.status_widget.height/2 - 25, 50, 50), 
                      width=2 + abs(self.animation_pulse))
    
    def activate_orion(self, instance):
        """Activa ORION"""
        self.is_active = True
        self.status_label.text = 'ORION activado 🎤'
        self.activate_button.opacity = 0
        self.input_container.opacity = 1
        self.text_input.focus = True
        
        # Animación de activación
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self.input_container)
    
    def send_command(self, instance):
        """Envía comando a ORION"""
        command = self.text_input.text.strip()
        if command:
            self.status_label.text = 'Procesando...'
            
            # Procesar en hilo separado
            thread = threading.Thread(
                target=self.process_command_background,
                args=(command,),
                daemon=True
            )
            thread.start()
            
            self.text_input.text = ''
    
    def process_command_background(self, command):
        """Procesa comando en background"""
        try:
            response = orion_process_command(command)
            
            # Actualizar UI en hilo principal
            Clock.schedule_once(lambda dt: self.update_response(response), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_response(f"Error: {str(e)}"), 0)
    
    def update_response(self, response):
        """Actualiza la respuesta en la UI"""
        self.status_label.text = response
        # Mantener activo para seguir conversando
        if not self.is_active:
            self.activate_orion(None)

if __name__ == '__main__':
    OrionMobileApp().run()
