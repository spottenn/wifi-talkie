FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Create recordings directory
RUN mkdir -p recordings

# Expose the WebSocket port
EXPOSE 8080

CMD ["python", "server.py"]
