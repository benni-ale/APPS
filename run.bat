@echo off
echo Building and running Stock Market Viewer...

REM Stop and remove any existing containers
docker stop stock-viewer 2>nul
docker rm stock-viewer 2>nul

REM Build the Docker image
echo Building Docker image...
docker build -t stock-viewer .

REM Run the container
echo Starting container...
docker run -d --name stock-viewer -p 5000:5000 -v %cd%/config.json:/app/config.json stock-viewer

echo.
echo Application is running!
echo.
echo IMPORTANT: Make sure you have created config.json with your Alpha Vantage API key
echo Copy config.example.json to config.json and update the API key
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