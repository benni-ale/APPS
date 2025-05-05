import os
import json
import time
import argparse
import logging
import random
from datetime import datetime, timedelta
from news_analyzer import get_news_sentiment, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='orchestrator.log'
)
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

def load_sp500_tickers(file_path="sp500_tickers.txt"):
    """Load S&P 500 tickers from a file"""
    try:
        with open(file_path, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(tickers)} tickers from {file_path}")
        return tickers
    except FileNotFoundError:
        logger.error(f"S&P 500 tickers file {file_path} not found. Creating a sample file.")
        sample_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ", 
                         "WMT", "PG", "MA", "HD", "BAC", "DIS", "ADBE", "CRM", "CMCSA", "XOM", 
                         "NFLX", "VZ", "INTC", "CSCO", "PFE", "KO", "PEP", "MRK", "T", "ABT"]
        with open(file_path, 'w') as f:
            f.write('\n'.join(sample_tickers))
        return sample_tickers

def generate_monthly_ranges(start_year, start_month, end_year, end_month):
    """Generate daily date ranges"""
    date_ranges = []
    
    # Convert input to datetime objects
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)
    
    # Calculate the last day of the end month
    if end_month == 12:
        next_month = 1
        next_year = end_year + 1
    else:
        next_month = end_month + 1
        next_year = end_year
    
    end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
    
    # Generate daily ranges
    current_date = start_date
    while current_date <= end_date:
        time_from = current_date.strftime('%Y%m%dT0000')
        time_to = current_date.strftime('%Y%m%dT2359')
        
        date_ranges.append({
            'from': time_from,
            'to': time_to,
            'label': current_date.strftime('%Y-%m-%d')
        })
        
        current_date += timedelta(days=1)
    
    logger.info(f"Generated {len(date_ranges)} daily ranges from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    return date_ranges

def create_random_ticker_groups(tickers, group_size=5, randomize=True):
    """Create random groups of tickers"""
    if randomize:
        # Create a copy of the tickers list to avoid modifying the original
        tickers_copy = tickers.copy()
        # Shuffle the copy
        random.shuffle(tickers_copy)
        # Split into groups
        return [tickers_copy[i:i + group_size] for i in range(0, len(tickers_copy), group_size)]
    else:
        # Original sequential grouping
        return [tickers[i:i + group_size] for i in range(0, len(tickers), group_size)]

def analyze_for_period_and_tickers(api_key, time_range, tickers, topics, output_dir, apply_ticker_filter=False):
    """Run analysis for a specific time period and ticker group"""
    try:
        # Create specific output directory for this analysis
        period_label = time_range.get('label', 'unknown')
        
        # Use all tickers in the folder name
        ticker_label = '_'.join(tickers)
        specific_dir = os.path.join(output_dir, f"{period_label}_{ticker_label}")
        
        if not os.path.exists(specific_dir):
            os.makedirs(specific_dir)
            logger.info(f"Created output directory: {specific_dir}")
        
        # Get news data
        logger.info(f"Analyzing news for period {period_label} and tickers {tickers}")
        news_data = get_news_sentiment(
            api_key=api_key,
            tickers=tickers,
            topics=topics,
            time_from=time_range.get('from'),
            time_to=time_range.get('to'),
            apply_ticker_filter=apply_ticker_filter
        )
        
        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(specific_dir, f'news_analysis_{timestamp}.json')
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'period': period_label,
                'tickers': tickers,
                'total_articles': len(news_data),
                'articles': news_data,
                'status': 'ok' if news_data else 'no_data'
            }, f, indent=4)
        
        logger.info(f"Saved {len(news_data)} articles to {filename}")
        return len(news_data)
    
    except Exception as e:
        logger.error(f"Error analyzing for period {time_range.get('label')} and tickers {tickers}: {str(e)}")
        return 0

def run_orchestrator(config_file='disconnected/config.json', ticker_file='disconnected/sp500_tickers.txt', 
                    start_date=None, end_date=None, ticker_group_size=10,
                    delay_between_calls=12, max_api_calls_per_minute=5,
                    randomize_tickers=True):
    """Main orchestrator function"""
    try:
        # Load config and tickers
        config = load_config(config_file)
        all_tickers = load_sp500_tickers(ticker_file)
        
        # Parse date ranges
        if start_date and end_date:
            # Parse custom date range with daily precision
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                start_year = start_dt.year
                start_month = start_dt.month
                end_year = end_dt.year
                end_month = end_dt.month
            except ValueError:
                logger.error("Invalid date format. Please use YYYY-MM-DD format")
                return
        else:
            # Use config file date range
            time_range = config.get('time_range', {})
            start_date_str = time_range.get('from', '')
            end_date_str = time_range.get('to', '')
            
            if not (start_date_str and end_date_str):
                logger.error("Date range not specified in config file")
                return
            
            # Parse dates from config (format: YYYYMMDDTHHMM)
            start_year = int(start_date_str[:4])
            start_month = int(start_date_str[4:6])
            end_year = int(end_date_str[:4])
            end_month = int(end_date_str[4:6])
        
        date_ranges = generate_monthly_ranges(start_year, start_month, end_year, end_month)
        logger.info(f"Generated {len(date_ranges)} date ranges from {start_year}-{start_month} to {end_year}-{end_month}")
        
        # Get other parameters from config
        api_key = config.get('api_key')
        topics = config.get('topics', ['earnings', 'technology', 'finance', 'markets', 'economy', 'business'])
        output_dir = config.get('output_dir', 'output')
        apply_ticker_filter = config.get('apply_ticker_filter', False)
        
        # Create base output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created base output directory: {output_dir}")
        
        # Track API calls to stay within rate limits
        api_calls = 0
        minute_start_time = time.time()
        total_articles = 0
        retry_count = 0
        max_retries = 3
        
        # Run analysis for each date range
        for date_range in date_ranges:
            # For each date range, create a new random grouping of tickers
            ticker_groups = create_random_ticker_groups(all_tickers, ticker_group_size, randomize_tickers)
            logger.info(f"Created {len(ticker_groups)} ticker groups for period {date_range['label']}")
            
            for group_idx, ticker_group in enumerate(ticker_groups):
                # Check API rate limits
                current_time = time.time()
                if current_time - minute_start_time >= 60:
                    api_calls = 0
                    minute_start_time = current_time
                
                if api_calls >= max_api_calls_per_minute:
                    wait_time = 60 - (current_time - minute_start_time) + 5  # Add buffer
                    logger.info(f"Rate limit approaching. Waiting {wait_time:.1f} seconds")
                    time.sleep(wait_time)
                    api_calls = 0
                    minute_start_time = time.time()
                
                # Run analysis with retry logic
                articles_found = 0
                while retry_count < max_retries:
                    try:
                        articles_found = analyze_for_period_and_tickers(
                            api_key, date_range, ticker_group, topics, output_dir, apply_ticker_filter
                        )
                        if articles_found > 0:
                            break
                        retry_count += 1
                        logger.warning(f"Retry {retry_count}/{max_retries} for period {date_range['label']}")
                        time.sleep(30)  # Wait before retry
                    except Exception as e:
                        logger.error(f"Error during analysis: {str(e)}")
                        retry_count += 1
                        time.sleep(30)
                
                total_articles += articles_found
                retry_count = 0  # Reset retry count for next group
                
                # Update API call count and wait between calls
                api_calls += 1
                logger.info(f"Completed run {group_idx+1}/{len(ticker_groups)} for period {date_range['label']}")
                logger.info(f"Waiting {delay_between_calls} seconds before next API call")
                time.sleep(delay_between_calls)
        
        logger.info(f"Orchestration complete. Total articles found: {total_articles}")
    
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='News Sentiment Analysis Orchestrator')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--tickers', default='sp500_tickers.txt', help='File containing ticker symbols')
    parser.add_argument('--start', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end', help='End date in YYYY-MM-DD format')
    parser.add_argument('--group-size', type=int, default=10, help='Number of tickers per group')
    parser.add_argument('--delay', type=int, default=12, help='Delay between API calls in seconds')
    parser.add_argument('--rate-limit', type=int, default=5, help='Maximum API calls per minute')
    parser.add_argument('--random', dest='randomize', action='store_true', help='Randomize ticker selection')
    parser.add_argument('--no-random', dest='randomize', action='store_false', help='Use sequential ticker selection')
    parser.set_defaults(randomize=True)
    
    args = parser.parse_args()
    
    run_orchestrator(
        config_file=args.config,
        ticker_file=args.tickers,
        start_date=args.start,
        end_date=args.end,
        ticker_group_size=args.group_size,
        delay_between_calls=args.delay,
        max_api_calls_per_minute=args.rate_limit,
        randomize_tickers=args.randomize
    ) 