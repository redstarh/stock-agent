# Stage 1: Build
FROM python:3.13-slim AS builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies to a separate location
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
