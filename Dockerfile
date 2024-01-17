FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
USER root:root

RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install

ENV PYTHONPATH="/app:/app/src"

EXPOSE 5000

CMD ["python", "/app/src/crawler_app.py"]