@echo off
REM ===== auto promote rules =====

cd /d C:\ollama\rag

"C:\Users\prest\AppData\Local\Programs\Python\Python311\python.exe" ^
  scripts\auto_promote_rules.py ^
  >> logs\promote_task.log 2>&1

exit /b %ERRORLEVEL%
