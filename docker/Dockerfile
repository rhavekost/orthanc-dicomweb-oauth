FROM jodogne/orthanc-python:latest

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir requests || apt-get update && apt-get install -y python3-pip && python3 -m pip install --no-cache-dir requests

# Copy plugin files
COPY src/dicomweb_oauth_plugin.py /etc/orthanc/plugins/
COPY src/token_manager.py /etc/orthanc/plugins/
COPY src/config_parser.py /etc/orthanc/plugins/
COPY src/__init__.py /etc/orthanc/plugins/

# Copy Orthanc configuration
COPY docker/orthanc.json /etc/orthanc/

# Expose ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

CMD ["/etc/orthanc/"]
