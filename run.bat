@echo off
setlocal
cd /d "%~dp0"

echo ===============================================
echo  Simulador de Entrevistas - RetailNova v0.1.1
echo ===============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual del simulador...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: No se pudo crear el entorno virtual.
        echo Verifique que Python este instalado.
        pause
        exit /b 1
    )
)

echo Instalando/verificando dependencias dentro del entorno virtual...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Servidor disponible en:
echo http://127.0.0.1:8000
echo.
echo Para detenerlo, presione CTRL+C.
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload

pause