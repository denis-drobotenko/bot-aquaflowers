FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Copy templates and static files
COPY templates/ ./templates/
COPY static/ ./static/

# Ensure prompts directory exists and copy prompts
RUN mkdir -p /app/src/services/prompts
COPY src/services/prompts/ ./src/services/prompts/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"] 