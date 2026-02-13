FROM jodogne/orthanc-python:latest

# Install Python dependencies via apt (externally-managed environment)
RUN apt-get update && apt-get install -y python3-requests && rm -rf /var/lib/apt/lists/*

# Copy entire src directory to maintain package structure
COPY src/ /etc/orthanc/plugins/src/

# Set Python path to include plugin directory
ENV PYTHONPATH=/etc/orthanc/plugins:$PYTHONPATH

# Copy Orthanc configuration
COPY docker/orthanc.json /etc/orthanc/

# Expose ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

CMD ["/etc/orthanc/"]
