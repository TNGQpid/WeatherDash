FROM python:3.11-slim

WORKDIR /app

COPY fetch_weather.py .

RUN pip install requests psycopg2-binary

CMD ["python", "fetch_weather.py"]