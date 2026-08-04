@echo off
cd /d %~dp0\..
call .venv\Scripts\activate.bat
python main.py >> workspace\daily.log 2>&1
