# Stock Market Viewer

A containerized web application that displays stock market data using Yahoo Finance API.

## Features

- Real-time stock data visualization
- Interactive candlestick charts
- Current price, market cap, and volume information
- Multiple time period options (1 day to 1 year)
- Modern dark-themed UI

## Requirements

- Docker
- Docker Compose (optional)

## Running the Application

### Using Docker

1. Build the Docker image:
```bash
docker build -t stock-viewer .
```

2. Run the container:
```bash
docker run -p 5000:5000 stock-viewer
```

### Using Docker Compose

1. Run the application:
```bash
docker-compose up
```

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Enter a stock symbol (e.g., AAPL for Apple, GOOGL for Google)
3. Select a time period
4. Click "Search" or press Enter

## Example Stock Symbols

- AAPL (Apple)
- GOOGL (Google)
- MSFT (Microsoft)
- AMZN (Amazon)
- TSLA (Tesla)
- FB (Meta)
- NFLX (Netflix) 