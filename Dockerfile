# ============================================================
# Multi-target Dockerfile for OpenVAS MCP Server and CLI
#
# Build targets:
#   docker build --target mcp -t openvas-mcp-server .
#   docker build --target cli -t openvas-cli .
# ============================================================

# === Shared builder ===
FROM python:3.12-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy dependency files and README (required by Poetry for package install)
COPY pyproject.toml poetry.lock* README.md ./

# Configure Poetry to not use virtualenvs in container
RUN poetry config virtualenvs.create false

# Install dependencies only (no dev deps)
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Copy source code
COPY src ./src

# Install the package
RUN poetry install --no-interaction --no-ansi --only main


# === Shared runtime base ===
FROM python:3.12-slim AS base

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


# === MCP Server ===
FROM base AS mcp

ENV MCP_TRANSPORT=stdio

# Expose HTTP port for streamable-http/sse transports
EXPOSE 8000

ENTRYPOINT ["openvas-mcp"]


# === CLI (toolbox container — used via docker exec) ===
FROM base AS cli

CMD ["sleep", "infinity"]
