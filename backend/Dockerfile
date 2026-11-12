FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r /app/backend/requirements.txt

COPY backend /app/backend
COPY data/processed /app/data/processed

EXPOSE 3001

CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "3001"]
