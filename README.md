# Stock Market Viewer

A containerized web application that displays stock market data using Alpha Vantage API.

## Features

- Real-time stock data visualization
- Interactive candlestick charts
- Current price, market cap, and volume information
- Multiple time period options (1 day to 1 year)
- Modern dark-themed UI

## Requirements

- Docker
- Docker Compose (optional)
- Alpha Vantage API key (get it from [here](https://www.alphavantage.co/support/#api-key))

## Configuration

1. Copy the example configuration file:
```bash
cp config.example.json config.json
```

2. Edit `config.json` and replace `your_api_key_here` with your Alpha Vantage API key:
```json
{
    "alpha_vantage_api_key": "your_api_key_here"
}
```

## Running the Application

### Using Docker

1. Build the Docker image:
```bash
docker build -t stock-viewer .
```

2. Run the container:
```bash
docker run -p 5000:5000 -v $(pwd)/config.json:/app/config.json stock-viewer
```

### Using run.bat (Windows)

1. Simply double-click `run.bat`
2. Open your browser and go to `http://localhost:5000`

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
- META (Meta)
- NFLX (Netflix) 