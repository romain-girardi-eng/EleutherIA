FROM python:3.11-slim

# Force cache bust - files migrated from LFS to regular git
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY backend/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code from backend directory
COPY backend/ /app/

# Copy Knowledge Graph database from root directory
COPY ancient_free_will_database.json /app/ancient_free_will_database.json

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
