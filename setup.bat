@echo off
echo Starting Dell Driver Scraper setup...

REM Check if Docker is installed
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed or not in PATH.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Start containers
echo Starting containers...
docker compose up -d

REM Wait for Ollama container to be ready
echo Waiting for Ollama container to initialize...
timeout /t 10 /nobreak > nul

REM Pull Llama3 model
echo Downloading Llama3 model for Ollama (this may take several minutes)...
docker exec -it ollama ollama pull llama3

echo.
echo Setup completed successfully!
echo.
echo Dell Driver Scraper is now available at: http://localhost:8501
echo.

pause