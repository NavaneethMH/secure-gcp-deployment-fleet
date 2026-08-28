FROM python:3.12.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY tests/cloud-run-demo/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY tests/cloud-run-demo/app.py ./app.py

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]