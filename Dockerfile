FROM python:3.12-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not use virtualenvs in container
RUN poetry config virtualenvs.create false

# Install dependencies only (no dev deps)
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Copy source code
COPY src ./src

# Install the package
RUN poetry install --no-interaction --no-ansi --only main


FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# MCP server runs on stdio by default
ENTRYPOINT ["openvas-mcp"]
