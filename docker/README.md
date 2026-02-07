# Docker Configuration

## ⚠️ SECURITY WARNING

The default `orthanc.json` configuration is **FOR DEVELOPMENT ONLY** and has security features disabled for ease of testing.

**For production deployments:**
1. Use `orthanc-secure.json` as your base configuration
2. Enable authentication (`"AuthenticationEnabled": true`)
3. Change default passwords immediately
4. Enable SSL/TLS (`"Ssl": true`)
5. Review all security settings

**NEVER deploy the development configuration to production or any environment handling real patient data (PHI).**

## Configuration Files

### orthanc.json (Development)
- Authentication: ✅ Enabled (default credentials: orthanc/orthanc)
- Remote Access: Enabled
- SSL: Disabled
- Use for: Local development, testing only

### orthanc-secure.json (Production Template)
- Authentication: ✅ Enabled (must change password)
- Remote Access: Enabled with authentication
- SSL: ✅ Enabled
- Use for: Production deployments, staging environments

## Quick Start

1. Copy `.env.example` to `.env` and configure your OAuth credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. Start Orthanc with the plugin:
   ```bash
   docker-compose up -d
   ```

3. Access Orthanc at http://localhost:8042

4. View logs:
   ```bash
   docker-compose logs -f orthanc
   ```

## Testing the Plugin

Check plugin status:
```bash
curl http://localhost:8042/plugins
```

Test DICOMweb connection (will trigger OAuth token acquisition):
```bash
curl http://localhost:8042/dicom-web/studies
```

## Development Workflow

The `src/` directory is mounted as a volume, but Python plugins require an Orthanc restart to reload:

```bash
docker-compose restart orthanc
```

## Troubleshooting

**View plugin logs:**
```bash
docker-compose logs orthanc | grep "DICOMweb OAuth"
```

**Check token acquisition:**
Look for "Token acquired for server" in logs

**Verify configuration:**
```bash
docker-compose exec orthanc cat /etc/orthanc/orthanc.json
```
