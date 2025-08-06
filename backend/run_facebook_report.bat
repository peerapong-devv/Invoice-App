@echo off
cd /d %~dp0
venv\Scripts\python generate_facebook_full_report.py
pause