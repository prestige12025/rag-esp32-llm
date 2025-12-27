@echo off
REM ===== auto demote rules =====

cd /d C:\ollama\rag

"C:\Users\prest\AppData\Local\Programs\Python\Python311\python.exe" ^
  scripts\auto_demote_rules.py ^
  >> logs\demote_task.log 2>&1

exit /b %ERRORLEVEL%
