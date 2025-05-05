import pandas as pd
import sqlite3
import hashlib
import json
import os
import shutil

def make_id(url, ticker):
    return hashlib.md5(f"{url}_{ticker}".encode()).hexdigest()

input_dir = "output"
processed_root = "processed"

# Connessione al DB
conn = sqlite3.connect("news.db")
cursor = conn.cursor()

# Crea tabella finale se non esiste
cursor.execute("""
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    source TEXT,
    time_published TEXT,
    summary TEXT,
    overall_sentiment_score REAL,
    overall_sentiment TEXT,
    topic TEXT,
    ticker TEXT,
    relevance_score REAL,
    sentiment_score REAL,
    sentiment TEXT
);
""")

# Scorri tutti i file JSON dentro output/
for root, _, files in os.walk(input_dir):
    for filename in files:
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(root, filename)
        rel_path = os.path.relpath(filepath, input_dir)
        dest_path = os.path.join(processed_root, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            rows = []
            for a in data.get("articles", []):
                for ts in a.get("ticker_sentiments", []):
                    rows.append({
                        "id": make_id(a["url"], ts["ticker"]),
                        "title": a["title"],
                        "url": a["url"],
                        "source": a["source"],
                        "time_published": a["time_published"],
                        "summary": a["summary"],
                        "overall_sentiment_score": a["sentiment_scores"]["overall"],
                        "overall_sentiment": a["sentiment"],
                        "topic": a["topic"],
                        "ticker": ts["ticker"],
                        "relevance_score": ts["relevance_score"],
                        "sentiment_score": ts["sentiment_score"],
                        "sentiment": ts["sentiment"]
                    })

            if not rows:
                print(f"⚠️ Nessun articolo trovato in: {rel_path}")
                continue

            df_new = pd.DataFrame(rows)
            df_new.to_sql("staging_articles", conn, if_exists="replace", index=False)

            cursor.execute("""
            INSERT OR IGNORE INTO articles
            SELECT * FROM staging_articles;
            """)
            inserted_rows = cursor.rowcount
            conn.commit()
            cursor.execute("DROP TABLE staging_articles;")

            shutil.move(filepath, dest_path)
            print(f"✅ Processato e spostato: {rel_path} — Righe inserite: {inserted_rows}")

        except Exception as e:
            print(f"❌ Errore con {rel_path}: {e}")

# Rimuovi le cartelle vuote dentro output/
for root, dirs, _ in os.walk(input_dir, topdown=False):
    for d in dirs:
        dir_path = os.path.join(root, d)
        if not os.listdir(dir_path):
            os.rmdir(dir_path)
            print(f"🧹 Rimossa cartella vuota: {dir_path}")

conn.close()
