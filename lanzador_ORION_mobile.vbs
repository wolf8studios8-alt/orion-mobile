Set WinScriptHost = CreateObject("WScript.Shell")
' Lanzar ORION Mobile en modo invisible
WinScriptHost.Run Chr(34) & "C:\Users\Francisco\Desktop\NOVA\iniciar_ORION_mobile.bat" & Chr(34), 0
Set WinScriptHost = Nothing
