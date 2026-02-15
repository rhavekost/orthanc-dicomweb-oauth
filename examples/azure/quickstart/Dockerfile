# Use orthancteam image with latest SDK and all plugins
FROM orthancteam/orthanc:latest-full

# Install Python dependencies and gettext-base for envsubst
# Note: orthancteam image already has Python and many dependencies
RUN apt-get update && apt-get install -y \
    python3-requests \
    python3-jwt \
    python3-cryptography \
    python3-jsonschema \
    python3-prometheus-client \
    python3-flask-limiter \
    python3-redis \
    gettext-base \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy entire src directory to maintain package structure
COPY src/ /etc/orthanc/plugins/src/

# Copy schemas directory for config validation
COPY schemas/ /etc/orthanc/plugins/schemas/

# Set Python path to include plugin directory
ENV PYTHONPATH=/etc/orthanc/plugins

# Copy Orthanc configuration as template (will be processed at runtime)
COPY examples/azure/quickstart/orthanc.json /etc/orthanc/orthanc.json.template

# Copy and make entrypoint script executable
COPY examples/azure/quickstart/docker-entrypoint.sh /usr/local/bin/custom-entrypoint.sh
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

# Enable required plugins via symlinks (orthancteam pattern)
# CRITICAL: Load Python plugin FIRST (renamed to 00-python.so) to intercept routes before DICOMweb plugin
# PostgreSQL Index plugin for persistent metadata
# Azure Blob Storage plugin for persistent DICOM file storage
# Only link plugins that actually exist to avoid startup crashes
RUN mkdir -p /etc/orthanc/plugins && \
    cd /usr/share/orthanc/plugins-available && \
    for plugin in libOrthancPython.so libOrthancPostgreSQLIndex.so libOrthancAzureBlobStorage.so libOrthancDicomWeb.so libOrthancExplorer2.so libOrthancGdcm.so; do \
        if [ -f "$plugin" ]; then \
            if [ "$plugin" = "libOrthancPython.so" ]; then \
                ln -s /usr/share/orthanc/plugins-available/$plugin /etc/orthanc/plugins/00-$plugin; \
            else \
                ln -s /usr/share/orthanc/plugins-available/$plugin /etc/orthanc/plugins/; \
            fi; \
        fi; \
    done

# Expose ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]
