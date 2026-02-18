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

# Expose port
EXPOSE 8000

# Run as non-root user
USER diaguser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
