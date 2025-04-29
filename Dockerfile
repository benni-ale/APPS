FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy example config if no config exists
COPY config.example.json config.json

EXPOSE 5000

ENV ALPHA_VANTAGE_API_KEY=demo

CMD ["python", "app.py"] 