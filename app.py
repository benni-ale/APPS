from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime, timedelta
import os
from functools import lru_cache
import time

app = Flask(__name__)

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: config.json not found. Please copy config.example.json to config.json and update with your API key.")
        return {"alpha_vantage_api_key": "demo"}

config = load_config()
ALPHA_VANTAGE_API_KEY = config['alpha_vantage_api_key']
BASE_URL = 'https://www.alphavantage.co/query'

# Cache for 1 minute to respect API limits while maintaining fresh data
@lru_cache(maxsize=128)
def get_cached_data(url, params_str):
    return requests.get(url, params=json.loads(params_str)).json()

def get_api_data(function, symbol, **additional_params):
    params = {
        'function': function,
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY,
        **additional_params
    }
    # Convert params to string for caching
    params_str = json.dumps(params, sort_keys=True)
    return get_cached_data(BASE_URL, params_str)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    try:
        symbol = request.json['symbol']
        period = request.json.get('period', '1mo')
        
        # Get time series data
        if period in ['1d', '5d']:
            data = get_api_data('TIME_SERIES_INTRADAY', symbol, interval='5min', outputsize='full')
            time_series_key = 'Time Series (5min)'
        else:
            data = get_api_data('TIME_SERIES_DAILY', symbol, outputsize='full')
            time_series_key = 'Time Series (Daily)'

        if 'Error Message' in data:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol or API error'
            })

        # Get company overview
        overview = get_api_data('OVERVIEW', symbol)
        
        # Get global quote
        quote = get_api_data('GLOBAL_QUOTE', symbol)
        
        # Get SMA indicator
        sma = get_api_data('SMA', symbol, interval='daily', time_period='20', series_type='close')
        
        # Parse time series data
        time_series = data[time_series_key]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Filter data based on period
        if period == '1d':
            df = df[df.index >= (datetime.now() - timedelta(days=1))]
        elif period == '5d':
            df = df[df.index >= (datetime.now() - timedelta(days=5))]
        elif period == '1mo':
            df = df[df.index >= (datetime.now() - timedelta(days=30))]
        elif period == '3mo':
            df = df[df.index >= (datetime.now() - timedelta(days=90))]
        elif period == '6mo':
            df = df[df.index >= (datetime.now() - timedelta(days=180))]
        elif period == '1y':
            df = df[df.index >= (datetime.now() - timedelta(days=365))]

        # Rename columns
        df.columns = [col.split('. ')[1] for col in df.columns]
        
        # Add SMA if available
        if 'Technical Analysis: SMA' in sma:
            sma_data = pd.DataFrame.from_dict(sma['Technical Analysis: SMA'], orient='index')
            sma_data.index = pd.to_datetime(sma_data.index)
            sma_data = sma_data.sort_index()
            df['sma'] = sma_data['SMA']

        # Create plot
        fig = go.Figure()
        
        # Add candlestick
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'].astype(float),
            high=df['high'].astype(float),
            low=df['low'].astype(float),
            close=df['close'].astype(float),
            name='OHLC'
        ))
        
        # Add SMA if available
        if 'sma' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['sma'].astype(float),
                name='20-day SMA',
                line=dict(color='orange', width=2)
            ))

        # Update layout with premium styling
        fig.update_layout(
            title=f'{symbol} Stock Price',
            yaxis_title='Price',
            xaxis_title='Date',
            template='plotly_dark',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(0,0,0,0.5)"
            )
        )
        
        # Convert plot to JSON
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Get current quote data
        quote_data = quote.get('Global Quote', {})
        current_price = float(quote_data.get('05. price', 0))
        change_percent = quote_data.get('10. change percent', 'N/A')
        volume = int(quote_data.get('06. volume', 0))
        
        # Prepare company info
        company_info = {
            'current_price': current_price,
            'change_percent': change_percent,
            'volume': volume,
            'market_cap': overview.get('MarketCapitalization', 'N/A'),
            'pe_ratio': overview.get('PERatio', 'N/A'),
            'dividend_yield': overview.get('DividendYield', 'N/A'),
            '52_week_high': overview.get('52WeekHigh', 'N/A'),
            '52_week_low': overview.get('52WeekLow', 'N/A'),
            'company_name': overview.get('Name', symbol),
            'sector': overview.get('Sector', 'N/A'),
            'industry': overview.get('Industry', 'N/A'),
            'description': overview.get('Description', 'N/A')
        }
        
        return jsonify({
            'success': True,
            'graph': graphJSON,
            'info': company_info
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")  # Add logging
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 