FROM python:3.11-slim

WORKDIR /app

COPY app.py .

RUN useradd --create-home appuser

USER appuser

CMD ["python", "app.py"]