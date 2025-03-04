FROM bitnami/spark:3.4.1

USER root

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Create checkpoint directory
RUN mkdir -p /tmp/checkpoints

# Run the Spark job
CMD ["python3", "process_github_events.py"] 