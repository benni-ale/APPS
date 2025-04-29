@echo off
echo Building and running Stock Market Viewer...

REM Stop and remove any existing containers
docker stop stock-viewer 2>nul
docker rm stock-viewer 2>nul

REM Build the Docker image
echo Building Docker image...
docker build -t stock-viewer .

REM Run the container with environment variable
echo Starting container...
docker run -d --name stock-viewer -p 5000:5000 -e ALPHA_VANTAGE_API_KEY=3R4MH8UHDMFLIIPG stock-viewer

echo.
echo Application is running!
echo.
echo IMPORTANT: Please replace 'demo' with your Alpha Vantage API key
echo Get your free API key at: https://www.alphavantage.co/support/#api-key
echo.
echo Open your browser and go to: http://localhost:5000
echo.
echo Press any key to stop the application...
pause >nul

REM Stop and remove the container when done
echo Stopping container...
docker stop stock-viewer
docker rm stock-viewer

echo Done! 