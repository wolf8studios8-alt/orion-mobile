@echo off
:: Iniciar ORION Mobile - Versión Móvil
cd /d "C:\Users\Francisco\Desktop\NOVA"

:: Activar el entorno virtual
call .venv\Scripts\activate.bat

:: IMPORTANTE: Usamos pythonw.exe para que NO se abra la consola negra
start /b .venv\Scripts\pythonw.exe orion_mobile.py
exit
