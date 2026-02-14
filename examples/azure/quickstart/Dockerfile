FROM orthancteam/orthanc:24.12.1-full

# Install Python dependencies for OAuth plugin
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install --no-cache-dir \
        requests==2.31.0 \
        PyJWT==2.8.0 \
        cryptography==41.0.7 \
        redis==5.0.1 \
        prometheus-client==0.19.0 && \
    rm -rf /var/lib/apt/lists/*

# Copy OAuth plugin from repository root
# Build context should be repository root
COPY src/ /etc/orthanc/plugins/

# Plugin will be loaded via ORTHANC__PLUGINS environment variable
ENV ORTHANC__PLUGINS='["/etc/orthanc/plugins/dicomweb_oauth_plugin.py"]'

# Expose Orthanc HTTP and DICOM ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

# Run as non-root user
USER orthanc

CMD ["Orthanc", "/etc/orthanc/"]
