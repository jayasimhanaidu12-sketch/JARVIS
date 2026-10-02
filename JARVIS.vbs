' JARVIS Silent App Launcher
' Launches JARVIS using pythonw without showing a command prompt window

Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strAppDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = strAppDir

' Launch via pythonw.exe in current directory
objShell.Run "pythonw.exe main.py", 0, False
