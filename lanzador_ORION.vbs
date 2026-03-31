Set WinScriptHost = CreateObject("WScript.Shell")
' El 0 al final es la clave: 0 = Oculto, 1 = Normal
WinScriptHost.Run Chr(34) & "C:\Users\Francisco\Desktop\NOVA\iniciar_ORION.bat" & Chr(34), 0
Set WinScriptHost = Nothing