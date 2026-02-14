FROM orthancteam/orthanc:24.12.0-full

# Install Python dependencies for OAuth plugin
# Versions match requirements.txt
RUN apt-get update && \
    apt-get install -y python3-pip curl && \
    pip3 install --break-system-packages --no-cache-dir \
        requests==2.31.0 \
        PyJWT==2.11.0 \
        cryptography==42.0.0 \
        redis==5.3.1 \
        prometheus-client==0.19.0 \
        jsonschema==4.20.0 \
        flask-limiter==3.5.0 && \
    rm -rf /var/lib/apt/lists/*

# Copy OAuth plugin from repository root
# Build context MUST be repository root
COPY src/ /etc/orthanc/plugins/src/
COPY schemas/ /etc/orthanc/plugins/schemas/

# Set PYTHONPATH for plugin imports
ENV PYTHONPATH="/etc/orthanc/plugins:${PYTHONPATH}"
ENV ORTHANC__PLUGINS='["/etc/orthanc/plugins/src/dicomweb_oauth_plugin.py"]'

# Expose Orthanc HTTP and DICOM ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

# Run as non-root user
USER orthanc

CMD ["Orthanc", "/etc/orthanc/"]
