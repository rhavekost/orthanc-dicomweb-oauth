# API Rate Limiting

## Overview

The plugin implements rate limiting to prevent abuse and denial-of-service attacks. Each client IP is limited to a maximum number of requests per time window.

## Configuration

Configure rate limiting globally:

```json
{
  "DicomWebOAuth": {
    "RateLimitRequests": 10,
    "RateLimitWindowSeconds": 60,

    "Servers": {
      "my-server": {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "my-client-id",
        "ClientSecret": "my-secret"
      }
    }
  }
}
```

## Configuration Fields

- **RateLimitRequests**: Maximum requests per window (default: 10)
- **RateLimitWindowSeconds**: Time window in seconds (default: 60)

## Default Configuration

If not specified:
- 10 requests per 60 seconds (10 req/min)
- Applied per client IP address
- Applies to all API endpoints

## Response

When rate limit exceeded, API returns:

```json
HTTP/1.1 429 Too Many Requests

{
  "error": "Rate limit exceeded for '192.168.1.100': 10 requests per 60s",
  "max_requests": 10,
  "window_seconds": 60
}
```

## Security Benefits

- **Prevents brute force attacks**: Limits authentication attempts
- **Prevents DoS**: Limits excessive requests
- **Protects OAuth provider**: Prevents account lockout

## Monitoring

Rate limit violations are logged as security events:

```json
{
  "timestamp": "2026-02-07T12:00:00Z",
  "level": "WARNING",
  "message": "Security event: rate_limit_exceeded",
  "security_event": true,
  "event_type": "rate_limit_exceeded",
  "client_ip": "192.168.1.100",
  "endpoint": "/dicomweb-oauth/status",
  "max_requests": 10,
  "window_seconds": 60
}
```

## Recommended Limits

| Environment | Requests | Window | Rate |
|------------|----------|--------|------|
| Development | 100 | 60s | 100/min |
| Production | 10 | 60s | 10/min |
| High-traffic | 30 | 60s | 30/min |
