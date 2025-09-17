# Dynamic Taxonomy RAG Security Framework Docker Image
FROM python:3.11-slim

# Security hardening
RUN groupadd --gid 1000 dtrag && \
    useradd --uid 1000 --gid dtrag --shell /bin/bash --create-home dtrag

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY apps/security/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models for PII detection
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . /app/

# Set environment variables
ENV PYTHONPATH="/app"
ENV SECURITY_LEVEL="production"
ENV JWT_SECRET="change-this-in-production"
ENV DATABASE_URL="postgresql://dtrag:password@postgres:5432/dtrag_security"
ENV REDIS_URL="redis://redis:6379/0"

# Create necessary directories
RUN mkdir -p /app/audit_logs /app/compliance_data /app/scan_results && \
    chown -R dtrag:dtrag /app

# Switch to non-root user
USER dtrag

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/security/status || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "apps.security.main:app", "--host", "0.0.0.0", "--port", "8000"]