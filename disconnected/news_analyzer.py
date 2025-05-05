import requests
import json
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level for detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_api_key(api_key):
    base_url = "https://www.alphavantage.co/query"
    params = {
        'function': 'NEWS_SENTIMENT',
        'topics': 'technology',
        'time_from': (datetime.now() - timedelta(days=1)).strftime('%Y%m%dT0000'),
        'time_to': datetime.now().strftime('%Y%m%dT2359'),
        'sort': 'LATEST',
        'limit': 1,
        'apikey': api_key
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if 'Information' in data or 'Error Message' in data:
            logger.error(f"API Key Error: {data.get('Information') or data.get('Error Message')}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False

def load_config(config_path='config.json'):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.debug(f"Loaded configuration: {json.dumps(config, indent=2)}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file {config_path}")
        raise

def get_news_sentiment(api_key, tickers=None, topics=None, time_from=None, time_to=None, apply_ticker_filter=True):
    base_url = "https://www.alphavantage.co/query"
    if topics is None:
        topics = ['earnings']
    if time_from is None:
        time_from = (datetime.now() - timedelta(days=30)).strftime('%Y%m%dT0000')
    if time_to is None:
        time_to = datetime.now().strftime('%Y%m%dT2359')

    logger.debug(f"Making API call with parameters:")
    logger.debug(f"Tickers: {tickers}")
    logger.debug(f"Topics: {topics}")
    logger.debug(f"Time range: {time_from} to {time_to}")

    all_news = []

    for topic in topics:
        params = {
            'function': 'NEWS_SENTIMENT',
            'topics': topic,
            'time_from': time_from,
            'time_to': time_to,
            'sort': 'LATEST',
            'limit': 200,
            'apikey': api_key
        }
        if apply_ticker_filter and tickers:
            params['tickers'] = ','.join(tickers)
        else:
            logger.debug("Skipping 'tickers' filter to broaden results")

        try:
            logger.info(f"Fetching news for topic: {topic}")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if 'feed' in data:
                logger.info(f"Retrieved {len(data['feed'])} articles for topic {topic}")
                for item in data['feed']:
                    news_item = {
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', 'Unknown'),
                        'time_published': item.get('time_published', ''),
                        'summary': item.get('summary', ''),
                        'stocks_mentioned': [ticker['ticker'] for ticker in item.get('ticker_sentiment', [])],
                        'sentiment_scores': {
                            'overall': float(item.get('overall_sentiment_score', 0)),
                            'relevance': float(item.get('relevance_score', 0))
                        },
                        'sentiment': item.get('overall_sentiment_label', 'neutral'),
                        'topic': topic,
                        'ticker_sentiments': [
                            {
                                'ticker': ticker['ticker'],
                                'relevance_score': float(ticker['relevance_score']),
                                'sentiment_score': float(ticker['ticker_sentiment_score']),
                                'sentiment': ticker['ticker_sentiment_label']
                            } for ticker in item.get('ticker_sentiment', [])
                        ]
                    }
                    print(news_item)
                    all_news.append(news_item)
            else:
                logger.warning(f"No 'feed' data found in response for topic {topic}")
        except Exception as e:
            logger.error(f"Error fetching news for topic {topic}: {str(e)}")

    return all_news

def main():
    try:
        config = load_config()
        api_key = config.get('api_key')
        if not api_key or api_key == 'YOUR_API_KEY':
            logger.error("Please set a valid API key in config.json")
            return

        logger.info("Validating API key...")
        if not validate_api_key(api_key):
            logger.error("API key validation failed.")
            return

        output_dir = config.get('output_dir', 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")

        news_data = get_news_sentiment(
            api_key=api_key,
            tickers=config.get('tickers'),
            topics=config.get('topics'),
            time_from=config.get('time_range', {}).get('from'),
            time_to=config.get('time_range', {}).get('to'),
            apply_ticker_filter=config.get('apply_ticker_filter', True)
        )

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'news_analysis_{timestamp}.json')

        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_articles': len(news_data),
                'articles': news_data,
                'status': 'ok' if news_data else 'no_data'
            }, f, indent=4)

        logger.info(f"Data saved to {filename}")

    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == "__main__":
    main()