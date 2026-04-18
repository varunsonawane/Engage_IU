FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy frontend for StaticFiles serving (main.py looks at ../frontend relative to /app)
COPY frontend/ ./frontend/

# Data directory for SQLite persistence
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
