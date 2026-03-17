@echo off
:: 先更新 Espanso triggers，再啟動 Espanso
python "%~dp0gen_espanso.py"
"%LOCALAPPDATA%\Programs\Espanso\espansod.exe" launcher
