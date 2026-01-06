@echo off
chcp 65001 > nul
echo Generando arbol de directorios...
python generate_tree.py %1
pause