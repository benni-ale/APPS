FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV ALPHA_VANTAGE_API_KEY=demo

CMD ["python", "app.py"] 