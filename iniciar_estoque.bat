@echo off
title Estoque de Bebidas - Servidor
cd /d "%~dp0"

echo Verificando dependencias...
py -m pip install flask flask-login --quiet

echo.
echo Iniciando o sistema de estoque...
echo (Se for a primeira vez, use o arquivo "gerenciar_usuarios.bat" para criar seu login antes de continuar.)
echo.

start "" http://127.0.0.1:5000

py app.py

pause
