@echo off
echo Installing requirements...
pip install keyboard pyinstaller
echo Building exe...
pyinstaller --onefile --noconsole --uac-admin --icon mercys_anti_afk_valo.ico --add-data "mercys_anti_afk_valo.ico;." --name MercysAntiAFKValo mercys_anti_afk_valo.py
echo.
echo Done! Your app is in the "dist" folder: dist\MercysAntiAFKValo.exe
pause
