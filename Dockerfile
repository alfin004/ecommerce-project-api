# Use a lightweight Python image
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install dependencies first (better for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose internal container port (can stay 8000)
EXPOSE 8000

# Default command to run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
