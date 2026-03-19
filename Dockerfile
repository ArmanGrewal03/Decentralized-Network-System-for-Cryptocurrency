FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
WORKDIR /app/backend
RUN python generate_grpc.py

COPY frontend/ /app/frontend/

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend
EXPOSE 8000 50051

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
