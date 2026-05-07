@echo off
setlocal

echo ========================================
echo  QuoteRetriever Setup
echo ========================================
echo.

:: ------------------------------------------
:: 1. Check for Python
:: ------------------------------------------
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your PATH.
    echo         Please install Python 3.12+ from https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [OK] Found %PYTHON_VERSION%

:: ------------------------------------------
:: 2. Check for Docker
:: ------------------------------------------
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker was not found on your PATH.
    echo         Please install Docker Desktop from https://www.docker.com/get-started/
    exit /b 1
)
for /f "tokens=*" %%v in ('docker --version 2^>^&1') do set DOCKER_VERSION=%%v
echo [OK] Found %DOCKER_VERSION%

:: Check that the Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is installed but the daemon is not running.
    echo         Please start Docker Desktop and try again.
    exit /b 1
)
echo [OK] Docker daemon is running

echo.

:: ------------------------------------------
:: 3. Create venv and install dependencies
:: ------------------------------------------
if not exist ".ragsystem\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .ragsystem
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo Installing dependencies...
.ragsystem\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    exit /b 1
)
echo [OK] Dependencies installed

echo.

:: ------------------------------------------
:: 4. Start Qdrant Docker container
:: ------------------------------------------
docker inspect qdrant >nul 2>&1
if %errorlevel% equ 0 (
    :: Container exists, check if it's running
    for /f "tokens=*" %%s in ('docker inspect -f "{{.State.Running}}" qdrant 2^>^&1') do set QDRANT_RUNNING=%%s
    if "%QDRANT_RUNNING%"=="true" (
        echo [OK] Qdrant container is already running
    ) else (
        echo Starting existing Qdrant container...
        docker start qdrant >nul
        echo [OK] Qdrant container started
    )
) else (
    echo Creating and starting Qdrant container...
    docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v "%cd%\database:/qdrant/storage" qdrant/qdrant
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to start Qdrant container.
        exit /b 1
    )
    echo [OK] Qdrant container created and running
)

:: Wait for Qdrant to be ready
echo Waiting for Qdrant to be ready...
set RETRIES=0
:wait_loop
if %RETRIES% geq 15 (
    echo [ERROR] Qdrant did not become ready in time.
    exit /b 1
)
.ragsystem\Scripts\python -c "import urllib.request; urllib.request.urlopen('http://localhost:6333/healthz')" >nul 2>&1
if %errorlevel% neq 0 (
    set /a RETRIES+=1
    timeout /t 2 /nobreak >nul
    goto wait_loop
)
echo [OK] Qdrant is ready

echo.

:: ------------------------------------------
:: 5. Initialize database if collection does not exist
:: ------------------------------------------
echo Checking database collection...
pushd src
..\.ragsystem\Scripts\python update_database.py
if %errorlevel% neq 0 (
    echo [ERROR] Database initialization failed.
    popd
    exit /b 1
)
popd
echo [OK] Database is ready

echo.
echo ========================================
echo  Setup complete!
echo  Run the app with: .ragsystem\Scripts\streamlit run app.py
echo ========================================

endlocal
