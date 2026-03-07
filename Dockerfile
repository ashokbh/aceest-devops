# ---- Stage 1: Build / dependency install ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies in a virtual environment for clean copying
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: Runtime image ----
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN addgroup --system aceest && \
    adduser  --system --ingroup aceest aceest

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY app.py requirements.txt ./

# Ensure the DB and any outputs are written inside the container volume
RUN mkdir -p /app/data && chown aceest:aceest /app/data

# Switch to non-root user
USER aceest

# Make venv binaries the default
ENV PATH="/opt/venv/bin:$PATH" \
    DB_NAME="/app/data/aceest_fitness.db" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# Initialise DB then start the server
CMD ["sh", "-c", "python -c 'from app import init_db; init_db()' && python app.py"]
