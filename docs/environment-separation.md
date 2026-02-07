# Environment Separation Guide

## Overview

The plugin supports multiple environment configurations for development, staging, and production deployments.

## Available Environments

### Development (default)

**Purpose:** Local development and testing

**Config:** `docker/orthanc.json`

**Characteristics:**
- Weak authentication (`orthanc`/`orthanc`)
- SSL verification can be disabled
- Verbose logging
- Clear "DEVELOPMENT (INSECURE)" warning in name

**Start:**
```bash
cd docker
docker-compose up -d
```

### Staging

**Purpose:** Pre-production testing with production-like security

**Config:** `docker/orthanc-staging.json`

**Characteristics:**
- Strong authentication (environment-based)
- SSL verification REQUIRED
- Production-like OAuth endpoints
- Monitoring enabled

**Setup:**
```bash
cd docker

# Copy and configure
cp .env.staging.example .env.staging
nano .env.staging  # Fill in staging credentials

# Start with staging profile
docker-compose --profile staging up -d
```

### Production

**Purpose:** Production deployment

**Config:** `docker/orthanc-secure.json` (or custom)

**Characteristics:**
- Strong authentication REQUIRED
- SSL verification REQUIRED
- Audit logging enabled
- Monitoring and metrics
- Secret management via environment variables

**Setup:**
```bash
# Use environment variables, not .env files
export PROD_ORTHANC_PASSWORD=$(generate-secure-password)
export PROD_OAUTH_CLIENT_SECRET=$(get-from-vault)

# Start with production config
docker run -d \
  -v /path/to/orthanc-prod.json:/etc/orthanc/orthanc.json:ro \
  -e PROD_ORTHANC_PASSWORD \
  -e PROD_OAUTH_CLIENT_SECRET \
  orthancteam/orthanc:latest
```

## Environment Variables

### Development (.env)

```bash
# Orthanc (default weak credentials)
OAUTH_CLIENT_ID=dev-client-id
OAUTH_CLIENT_SECRET=dev-client-secret

# OAuth (test provider)
DICOM_URL=https://dev-dicom.example.com/
TOKEN_ENDPOINT=https://dev-login.example.com/oauth2/token
```

### Staging (.env.staging)

```bash
# Orthanc (strong credentials)
STAGING_ORTHANC_PASSWORD=generate-strong-password-here

# OAuth (staging provider)
STAGING_DICOM_URL=https://staging-dicom.example.com/
STAGING_TOKEN_ENDPOINT=https://login.staging.example.com/oauth2/token
STAGING_OAUTH_CLIENT_ID=staging-client-id
STAGING_OAUTH_CLIENT_SECRET=get-from-secure-vault
STAGING_OAUTH_SCOPE=https://dicom.example.com/.default
```

### Production (secrets manager)

**NEVER use .env files in production**

Use secrets manager:
- Azure Key Vault
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets

## Security Best Practices

### Development

✅ **DO:**
- Use dev environment only on localhost
- Keep it obviously insecure (force developers to use staging/prod configs)
- Test OAuth flows with dev credentials

❌ **DON'T:**
- Use dev config in staging/production
- Store dev credentials in password manager
- Enable external access to dev environment

### Staging

✅ **DO:**
- Use production-like security settings
- Test with staging OAuth endpoints
- Rotate credentials regularly
- Enable SSL verification
- Use strong passwords

❌ **DON'T:**
- Use production credentials in staging
- Disable SSL verification
- Skip authentication
- Use staging credentials elsewhere

### Production

✅ **DO:**
- Use secrets manager for all credentials
- Enable SSL verification ALWAYS
- Require authentication
- Enable audit logging
- Monitor for anomalies
- Rotate secrets regularly
- Use least-privilege OAuth scopes

❌ **DON'T:**
- Use .env files
- Commit credentials to git
- Disable security features
- Share production credentials
- Use wildcards in OAuth scopes

## Docker Compose Profiles

### Start Specific Environment

```bash
# Development (default)
docker-compose up -d

# Staging
docker-compose --profile staging up -d

# Multiple profiles
docker-compose --profile staging --profile monitoring up -d
```

### Check Running Environment

```bash
# Check which environment is running
curl http://localhost:8042/dicomweb-oauth/status | jq '.data'

# Should show environment in name
docker-compose ps
```

## Environment Detection

The plugin detects environment from config:

```json
{
  "Name": "Orthanc DICOMweb OAuth - STAGING Environment",
  ...
}
```

Extract environment:

```python
import requests

response = requests.get("http://localhost:8042/dicomweb-oauth/status")
name = response.json()["data"]["name"]

if "DEVELOPMENT" in name:
    print("Running in DEVELOPMENT")
elif "STAGING" in name:
    print("Running in STAGING")
elif "PRODUCTION" in name:
    print("Running in PRODUCTION")
```

## Troubleshooting

### "AuthenticationEnabled" Error

**Problem:** Cannot access Orthanc API

**Solution:** Check credentials for environment:
- Dev: `orthanc`/`orthanc`
- Staging: Check `.env.staging`
- Prod: Check secrets manager

### SSL Verification Error

**Problem:** `SSLError: certificate verify failed`

**Solution:**

**Development:** Disable SSL verification (for testing only)
```json
{
  "VerifySSL": false  // Development only!
}
```

**Staging/Production:** Fix certificate:
- Use valid SSL certificate
- Add CA certificate to trust store
- Check certificate expiration

### Wrong Environment Running

**Problem:** Staging using dev credentials

**Solution:**

```bash
# Stop all environments
docker-compose down

# Start specific environment
docker-compose --profile staging up -d

# Verify
curl http://localhost:8043/dicomweb-oauth/status | jq '.data'
```

## Migration Between Environments

### Dev → Staging

1. Update config with production-like security
2. Replace dev OAuth endpoints with staging
3. Enable SSL verification
4. Use strong credentials
5. Test thoroughly

### Staging → Production

1. Use secrets manager for credentials
2. Update OAuth endpoints to production
3. Enable all security features
4. Enable monitoring and alerting
5. Set up log aggregation
6. Document configuration
7. Create rollback plan

## Checklist

### Before Going to Staging

- [ ] AuthenticationEnabled: true
- [ ] VerifySSL: true
- [ ] Strong Orthanc password
- [ ] Staging OAuth credentials configured
- [ ] SSL certificate valid
- [ ] Logs reviewed
- [ ] Tests passing

### Before Going to Production

- [ ] All staging checks pass
- [ ] Secrets in secrets manager
- [ ] No .env files in production
- [ ] SSL certificate from trusted CA
- [ ] Monitoring configured
- [ ] Alerting configured
- [ ] Audit logging enabled
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Security review completed
- [ ] Load testing completed

## Additional Resources

- [Security Best Practices](security-best-practices.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Configuration Reference](configuration-reference.md)
