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
from top_companies import TOP_COMPANIES

app = Flask(__name__)

# Top 20 S&P500 companies (ticker, name, earnings, country, logo_url)
TOP_COMPANIES = [
    {"ticker": "AAPL", "name": "Apple", "earnings": "125.57B", "country": "USA", "logo": "https://logo.clearbit.com/apple.com"},
    {"ticker": "MSFT", "name": "Microsoft", "earnings": "89.47B", "country": "USA", "logo": "https://logo.clearbit.com/microsoft.com"},
    {"ticker": "GOOGL", "name": "Alphabet (Google)", "earnings": "73.80B", "country": "USA", "logo": "https://logo.clearbit.com/abc.xyz"},
    {"ticker": "AMZN", "name": "Amazon", "earnings": "30.43B", "country": "USA", "logo": "https://logo.clearbit.com/amazon.com"},
    {"ticker": "META", "name": "Meta Platforms", "earnings": "39.10B", "country": "USA", "logo": "https://logo.clearbit.com/meta.com"},
    {"ticker": "TSLA", "name": "Tesla", "earnings": "15.00B", "country": "USA", "logo": "https://logo.clearbit.com/tesla.com"},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway", "earnings": "115.57B", "country": "USA", "logo": "https://logo.clearbit.com/berkshirehathaway.com"},
    {"ticker": "NVDA", "name": "NVIDIA", "earnings": "29.76B", "country": "USA", "logo": "https://logo.clearbit.com/nvidia.com"},
    {"ticker": "JPM", "name": "JPMorgan Chase", "earnings": "48.33B", "country": "USA", "logo": "https://logo.clearbit.com/jpmorganchase.com"},
    {"ticker": "V", "name": "Visa", "earnings": "17.27B", "country": "USA", "logo": "https://logo.clearbit.com/visa.com"},
    {"ticker": "UNH", "name": "UnitedHealth Group", "earnings": "22.38B", "country": "USA", "logo": "https://logo.clearbit.com/unitedhealthgroup.com"},
    {"ticker": "XOM", "name": "Exxon Mobil", "earnings": "55.74B", "country": "USA", "logo": "https://logo.clearbit.com/exxonmobil.com"},
    {"ticker": "PG", "name": "Procter & Gamble", "earnings": "14.74B", "country": "USA", "logo": "https://logo.clearbit.com/pg.com"},
    {"ticker": "MA", "name": "Mastercard", "earnings": "11.19B", "country": "USA", "logo": "https://logo.clearbit.com/mastercard.com"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "earnings": "17.94B", "country": "USA", "logo": "https://logo.clearbit.com/jnj.com"},
    {"ticker": "LLY", "name": "Eli Lilly", "earnings": "5.24B", "country": "USA", "logo": "https://logo.clearbit.com/lilly.com"},
    {"ticker": "HD", "name": "Home Depot", "earnings": "17.10B", "country": "USA", "logo": "https://logo.clearbit.com/homedepot.com"},
    {"ticker": "MRK", "name": "Merck & Co.", "earnings": "14.52B", "country": "USA", "logo": "https://logo.clearbit.com/merck.com"},
    {"ticker": "ABBV", "name": "AbbVie", "earnings": "11.84B", "country": "USA", "logo": "https://logo.clearbit.com/abbvie.com"},
    {"ticker": "PEP", "name": "PepsiCo", "earnings": "9.08B", "country": "USA", "logo": "https://logo.clearbit.com/pepsico.com"}
]

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
        if time_series_key not in data or not isinstance(data[time_series_key], dict) or not data[time_series_key]:
            return jsonify({
                'success': False,
                'error': 'Dati non disponibili per questo simbolo o periodo. Prova a cambiare periodo o riprova più tardi.'
            })

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

@app.route('/api/top_companies')
def api_top_companies():
    api_key = config['alpha_vantage_api_key']
    results = []
    for company in TOP_COMPANIES:
        ticker = company['ticker']
        # Get GLOBAL_QUOTE
        quote_url = 'https://www.alphavantage.co/query'
        quote_params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': api_key
        }
        quote_resp = requests.get(quote_url, params=quote_params)
        quote_data = quote_resp.json().get('Global Quote', {})
        price = float(quote_data.get('05. price', 0))
        change = float(quote_data.get('09. change', 0))
        change_percent = quote_data.get('10. change percent', '0%')
        volume = int(quote_data.get('06. volume', 0))
        # Get OVERVIEW
        overview_url = 'https://www.alphavantage.co/query'
        overview_params = {
            'function': 'OVERVIEW',
            'symbol': ticker,
            'apikey': api_key
        }
        overview_resp = requests.get(overview_url, params=overview_params)
        overview_data = overview_resp.json()
        market_cap = overview_data.get('MarketCapitalization', 'N/A')
        pe_ratio = overview_data.get('PERatio', 'N/A')
        # Get sparkline (last 30 closes)
        ts_url = 'https://www.alphavantage.co/query'
        ts_params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'apikey': api_key,
            'outputsize': 'compact'
        }
        ts_resp = requests.get(ts_url, params=ts_params)
        ts_data = ts_resp.json().get('Time Series (Daily)', {})
        closes = []
        if ts_data:
            closes = [float(v['4. close']) for k, v in sorted(ts_data.items(), reverse=False)][-30:]
        # Compose result
        results.append({
            **company,
            'price': price,
            'change': change,
            'change_percent': change_percent,
            'volume': volume,
            'market_cap': market_cap,
            'pe_ratio': pe_ratio,
            'sparkline': closes
        })
    return jsonify({'companies': results})

@app.route('/sma')
def sma_plot():
    return render_template('sma.html')

@app.route('/close-volume')
def close_volume_plot():
    return render_template('close_volume.html')

@app.route('/search')
def search_company():
    return render_template('search.html')

@app.route('/marketcap')
def marketcap_view():
    return render_template('marketcap.html')

@app.route('/get_close_volume_data', methods=['POST'])
def get_close_volume_data():
    try:
        symbol = request.json['symbol']
        period = request.json.get('period', '1mo')
        # Recupera dati daily
        data = get_api_data('TIME_SERIES_DAILY', symbol, outputsize='full')
        time_series_key = 'Time Series (Daily)'
        if 'Error Message' in data or time_series_key not in data or not isinstance(data[time_series_key], dict) or not data[time_series_key]:
            return jsonify({'success': False, 'error': 'Dati non disponibili per questo simbolo o periodo.'})
        time_series = data[time_series_key]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        # Filtra periodo
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
        # Estrai close e volume
        df['close'] = df['4. close'].astype(float)
        df['volume'] = df['5. volume'].astype(float)
        # Normalizza volume tra 0 e 1
        min_vol = df['volume'].min()
        max_vol = df['volume'].max()
        if max_vol > min_vol:
            df['volume_norm'] = (df['volume'] - min_vol) / (max_vol - min_vol)
        else:
            df['volume_norm'] = 0
        # Prepara dati per il frontend
        return jsonify({
            'success': True,
            'dates': [d.strftime('%Y-%m-%d') for d in df.index],
            'close': df['close'].tolist(),
            'volume_norm': df['volume_norm'].tolist()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 