FROM python:3.11-slim

WORKDIR /app

# Using repo root as build context
COPY dt-rag/packages/common-schemas /packages/common-schemas
RUN pip install -e /packages/common-schemas

# App code
COPY dt-rag/apps/api/ ./
RUN pip install -r requirements.txt

# Healthcheck dependency
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]