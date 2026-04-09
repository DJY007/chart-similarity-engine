FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY scripts ./scripts

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/data/uploads

# Expose port
EXPOSE 8000

# Run the application using shell form to expand environment variables
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"


