FROM python:3.11-slim AS base

# Install Graphviz
RUN apt-get update && \
    apt-get install -y --no-install-recommends graphviz && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for sandboxed execution
RUN useradd --create-home --shell /bin/bash diaguser

WORKDIR /usr/src/app

# Copy the diagrams library from the repo root
COPY diagrams/ /usr/src/diagrams/diagrams/
COPY resources/ /usr/src/diagrams/resources/
COPY pyproject.toml /usr/src/diagrams/pyproject.toml

# Install the diagrams library
RUN pip install --no-cache-dir /usr/src/diagrams

# Copy and install backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/app ./app

# Expose ports: 8000 for FastAPI, 8088 for Foundry hosting adapter
EXPOSE 8000
EXPOSE 8088

# Run as non-root user
USER diaguser

# Default: run FastAPI. For Foundry deployment, override CMD with hosting adapter.
# Foundry entrypoint: python -m azure.ai.agentserver
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
