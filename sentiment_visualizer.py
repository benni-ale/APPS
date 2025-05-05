import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
from news_analyzer import get_news_sentiment

class SentimentVisualizer:
    def __init__(self, api_key, output_dir='sentiment_plots'):
        self.api_key = api_key
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def plot_sentiment_over_time(self, ticker, start_date, end_date, save_plot=True):
        """
        Genera un grafico dell'andamento del sentiment per un ticker specifico
        in un determinato periodo di tempo.
        
        Args:
            ticker (str): Il simbolo del ticker (es. 'AAPL')
            start_date (str): Data di inizio nel formato 'YYYYMMDDTHHMM'
            end_date (str): Data di fine nel formato 'YYYYMMDDTHHMM'
            save_plot (bool): Se True, salva il grafico come immagine
        """
        # Ottieni le news per il ticker
        news = get_news_sentiment(
            api_key=self.api_key,
            tickers=[ticker],
            time_from=start_date,
            time_to=end_date
        )

        if not news:
            print(f"Nessuna news trovata per {ticker} nel periodo specificato")
            return None

        # Raggruppa le news per giorno e calcola l'average sentiment
        daily_sentiment = {}
        for item in news:
            date = datetime.strptime(item['time_published'], '%Y%m%dT%H%M%S').date()
            if date not in daily_sentiment:
                daily_sentiment[date] = []
            daily_sentiment[date].append(item['sentiment_scores']['overall'])

        # Calcola l'average sentiment per ogni giorno
        dates = []
        avg_sentiments = []
        for date, sentiments in sorted(daily_sentiment.items()):
            dates.append(date)
            avg_sentiments.append(sum(sentiments) / len(sentiments))

        # Crea il grafico
        plt.figure(figsize=(12, 6))
        plt.plot(dates, avg_sentiments, marker='o', linestyle='-', linewidth=2)
        plt.title(f'Average Sentiment for {ticker} over Time', fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Average Sentiment Score', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Aggiungi una linea orizzontale a y=0 per riferimento
        plt.axhline(y=0, color='r', linestyle='--', alpha=0.3)

        if save_plot:
            # Salva il grafico
            filename = f"{ticker}_{start_date[:8]}_{end_date[:8]}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath)
            print(f"Grafico salvato in: {filepath}")
        
        plt.show()
        return dates, avg_sentiments

    def save_sentiment_data(self, ticker, dates, sentiments, filename=None):
        """
        Salva i dati del sentiment in un file JSON
        """
        if filename is None:
            filename = f"{ticker}_sentiment_data.json"
        
        data = {
            'ticker': ticker,
            'sentiment_data': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'sentiment': sentiment
                }
                for date, sentiment in zip(dates, sentiments)
            ]
        }
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"Dati salvati in: {filepath}")

def main():
    # Esempio di utilizzo
    from config import API_KEY  # Assumi di avere un file config.py con la tua API key
    
    visualizer = SentimentVisualizer(api_key=API_KEY)
    
    # Esempio: analizza il sentiment di Apple per l'ultimo mese
    ticker = 'AAPL'
    end_date = datetime.now().strftime('%Y%m%dT%H%M%S')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%dT%H%M%S')
    
    dates, sentiments = visualizer.plot_sentiment_over_time(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date
    )
    
    # Salva i dati
    visualizer.save_sentiment_data(ticker, dates, sentiments)

if __name__ == "__main__":
    main() 