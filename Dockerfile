FROM python:3.11-slim

WORKDIR /app

# Копируем все файлы из app/ в /app контейнера
COPY ./app/ .

RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader punkt wordnet

# Дополнительный CMD для CLI (будет переопределен в docker-compose)
CMD ["python", "web_interface.py"]