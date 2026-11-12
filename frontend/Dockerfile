FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r /app/requirements.txt

COPY frontend /app/frontend
COPY scripts/smoke_compose.py /app/smoke_compose.py

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
