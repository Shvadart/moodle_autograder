FROM python:3.11-slim

WORKDIR /app

COPY app/ /app/

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install flask && \
    python -m nltk.downloader punkt wordnet

# Создаем директорию для шаблонов
RUN mkdir -p /app/templates

CMD ["python", "-u", "web_interface.py"]