FROM jodogne/orthanc-python:latest

# Install Python dependencies via apt (externally-managed environment)
# Maps to requirements.txt: requests, PyJWT, cryptography, jsonschema, prometheus-client, flask-limiter, redis
RUN apt-get update && apt-get install -y \
    python3-requests \
    python3-jwt \
    python3-cryptography \
    python3-jsonschema \
    python3-prometheus-client \
    python3-flask-limiter \
    python3-redis \
    && rm -rf /var/lib/apt/lists/*

# Copy entire src directory to maintain package structure
COPY src/ /etc/orthanc/plugins/src/

# Copy schemas directory for config validation
COPY schemas/ /etc/orthanc/plugins/schemas/

# Set Python path to include plugin directory
ENV PYTHONPATH=/etc/orthanc/plugins

# Copy Orthanc configuration
COPY docker/orthanc.json /etc/orthanc/

# Expose ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

CMD ["/etc/orthanc/"]
