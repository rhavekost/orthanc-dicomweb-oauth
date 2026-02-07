# HIPAA Audit Logging Guide

This document provides guidance on configuring and managing audit logs for HIPAA compliance.

## Overview

**Requirement:** 45 CFR § 164.312(b) requires implementation of hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information (ePHI).

## What Must Be Logged

### HIPAA-Required Events

According to HIPAA Security Rule and industry best practices, log the following:

**Access Events:**
- ✅ User login/logout (authentication)
- ✅ Token acquisition and validation
- ✅ Failed authentication attempts
- ✅ Authorization failures (insufficient permissions)
- ✅ Session timeouts/expiration

**Data Access Events:**
- ✅ ePHI access (DICOM study retrieval, search)
- ✅ Data modification (upload, delete)
- ✅ Data export/download
- ✅ Queries and searches performed

**System Events:**
- ✅ Configuration changes
- ✅ Security policy changes
- ✅ Service start/stop
- ✅ Software updates
- ✅ Emergency access usage

**Security Events:**
- ✅ Rate limiting triggers
- ✅ Suspicious activity detection
- ✅ Intrusion detection alerts
- ✅ Malware detection
- ✅ Policy violations

## Audit Log Format

### Structured Logging (JSON)

All audit logs use structured JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2026-02-07T15:30:00.123456Z",
  "level": "INFO",
  "correlation_id": "req-abc123-def456",
  "event_type": "TOKEN_ACQUIRED",
  "user_id": "user@example.com",
  "source_ip": "203.0.113.45",
  "user_agent": "Mozilla/5.0 ...",
  "action": "authenticate",
  "resource": "server:azure-dicomweb",
  "result": "SUCCESS",
  "response_time_ms": 45,
  "details": {
    "oauth_provider": "azure",
    "token_lifetime": 3600,
    "scopes": ["dicomweb.read", "dicomweb.write"]
  }
}
```

### Required Fields

Every audit log entry MUST include:

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | ISO 8601 UTC timestamp with microseconds | `2026-02-07T15:30:00.123456Z` |
| `level` | Log level (INFO, WARN, ERROR) | `INFO` |
| `correlation_id` | Unique identifier for request tracing | `req-abc123-def456` |
| `event_type` | Type of event | `TOKEN_ACQUIRED` |
| `user_id` | User identifier from OAuth token | `user@example.com` |
| `source_ip` | IP address of client | `203.0.113.45` |
| `action` | Action performed | `authenticate` |
| `resource` | Resource accessed | `server:azure-dicomweb` |
| `result` | SUCCESS or FAILURE | `SUCCESS` |

### Optional Fields

Additional context when available:

| Field | Description | Example |
|-------|-------------|---------|
| `user_agent` | Client user agent string | `Mozilla/5.0 ...` |
| `response_time_ms` | Request processing time | `45` |
| `error_code` | Error code if failure | `INVALID_TOKEN` |
| `error_message` | Error description | `Token signature invalid` |
| `details` | Additional event-specific data | `{"oauth_provider": "azure"}` |

## Event Types

### Authentication Events

**TOKEN_ACQUIRED**
```json
{
  "event_type": "TOKEN_ACQUIRED",
  "user_id": "user@example.com",
  "result": "SUCCESS",
  "details": {
    "oauth_provider": "azure",
    "grant_type": "client_credentials",
    "token_lifetime": 3600
  }
}
```

**TOKEN_VALIDATION_FAILED**
```json
{
  "event_type": "TOKEN_VALIDATION_FAILED",
  "user_id": "unknown",
  "result": "FAILURE",
  "error_code": "INVALID_SIGNATURE",
  "error_message": "JWT signature verification failed",
  "details": {
    "token_header": {"alg": "HS256", "typ": "JWT"}
  }
}
```

**AUTHENTICATION_FAILED**
```json
{
  "event_type": "AUTHENTICATION_FAILED",
  "user_id": "attacker@example.com",
  "result": "FAILURE",
  "error_code": "INVALID_CREDENTIALS",
  "details": {
    "attempt_count": 3,
    "source_ip": "192.0.2.100"
  }
}
```

### Authorization Events

**AUTHORIZATION_FAILED**
```json
{
  "event_type": "AUTHORIZATION_FAILED",
  "user_id": "user@example.com",
  "result": "FAILURE",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "resource": "server:protected-server",
  "details": {
    "required_scope": "dicomweb.admin",
    "user_scopes": ["dicomweb.read"]
  }
}
```

### Cache Events

**TOKEN_CACHED**
```json
{
  "event_type": "TOKEN_CACHED",
  "user_id": "system",
  "result": "SUCCESS",
  "details": {
    "cache_backend": "redis",
    "cache_key": "token:azure-dicomweb",
    "ttl_seconds": 3540
  }
}
```

**CACHE_HIT**
```json
{
  "event_type": "CACHE_HIT",
  "user_id": "system",
  "result": "SUCCESS",
  "response_time_ms": 2,
  "details": {
    "cache_backend": "redis",
    "cache_key": "token:azure-dicomweb"
  }
}
```

**CACHE_MISS**
```json
{
  "event_type": "CACHE_MISS",
  "user_id": "system",
  "result": "SUCCESS",
  "details": {
    "cache_backend": "redis",
    "cache_key": "token:azure-dicomweb",
    "reason": "expired"
  }
}
```

### Rate Limiting Events

**RATE_LIMIT_EXCEEDED**
```json
{
  "event_type": "RATE_LIMIT_EXCEEDED",
  "user_id": "user@example.com",
  "source_ip": "203.0.113.45",
  "result": "FAILURE",
  "error_code": "TOO_MANY_REQUESTS",
  "details": {
    "limit": 60,
    "window_seconds": 60,
    "current_count": 75
  }
}
```

### Configuration Events

**CONFIGURATION_LOADED**
```json
{
  "event_type": "CONFIGURATION_LOADED",
  "user_id": "system",
  "result": "SUCCESS",
  "details": {
    "config_file": "/etc/orthanc/orthanc.json",
    "servers_configured": 3,
    "cache_backend": "redis"
  }
}
```

**CONFIGURATION_ERROR**
```json
{
  "event_type": "CONFIGURATION_ERROR",
  "user_id": "system",
  "result": "FAILURE",
  "error_code": "INVALID_CONFIGURATION",
  "error_message": "Missing required field: OAuth.ClientId",
  "details": {
    "config_file": "/etc/orthanc/orthanc.json",
    "validation_errors": ["OAuth.ClientId is required"]
  }
}
```

## Log Configuration

### Basic Configuration

```json
{
  "OAuth": {
    "AuditLogging": {
      "Enabled": true,
      "LogLevel": "INFO",
      "Format": "json",
      "IncludeUserIdentity": true,
      "IncludeSourceIP": true,
      "IncludeUserAgent": true,
      "RedactSensitiveData": true
    }
  }
}
```

### Log Levels

| Level | Events Logged | Use Case |
|-------|--------------|----------|
| **ERROR** | Only errors and failures | Production minimal logging |
| **WARN** | Errors + warnings (rate limits, expired tokens) | Production recommended |
| **INFO** | All events including successful operations | Production HIPAA compliance |
| **DEBUG** | Detailed debugging information | Development/troubleshooting |

**HIPAA Recommendation:** Use **INFO** level for compliance.

### Log Destinations

#### CloudWatch Logs (AWS)

```json
{
  "OAuth": {
    "AuditLogging": {
      "Destination": "cloudwatch",
      "CloudWatch": {
        "LogGroup": "/aws/orthanc/oauth",
        "LogStream": "instance-{instance-id}",
        "Region": "us-east-1"
      }
    }
  }
}
```

**Query Example:**
```
fields @timestamp, user_id, event_type, result
| filter event_type = "TOKEN_VALIDATION_FAILED"
| stats count() by user_id
```

#### Azure Monitor (Azure)

```json
{
  "OAuth": {
    "AuditLogging": {
      "Destination": "azure-monitor",
      "AzureMonitor": {
        "WorkspaceId": "xxxxx-xxxxx-xxxxx-xxxxx",
        "LogType": "OrthancOAuth"
      }
    }
  }
}
```

**Query Example (KQL):**
```kusto
OrthancOAuth_CL
| where event_type_s == "AUTHENTICATION_FAILED"
| summarize count() by source_ip_s
| order by count_ desc
```

#### Cloud Logging (GCP)

```json
{
  "OAuth": {
    "AuditLogging": {
      "Destination": "cloud-logging",
      "CloudLogging": {
        "ProjectId": "my-project",
        "LogName": "orthanc-oauth"
      }
    }
  }
}
```

**Query Example:**
```
resource.type="gce_instance"
jsonPayload.event_type="RATE_LIMIT_EXCEEDED"
```

#### File-based Logging

```json
{
  "OAuth": {
    "AuditLogging": {
      "Destination": "file",
      "File": {
        "Path": "/var/log/orthanc/oauth-audit.log",
        "MaxSizeMB": 100,
        "MaxBackups": 10,
        "Compress": true
      }
    }
  }
}
```

#### Syslog

```json
{
  "OAuth": {
    "AuditLogging": {
      "Destination": "syslog",
      "Syslog": {
        "Server": "syslog.example.com",
        "Port": 514,
        "Protocol": "tcp",
        "Facility": "local0",
        "TLS": true
      }
    }
  }
}
```

## Log Retention

### HIPAA Requirements

**Retention Period:**
- **Minimum:** 6 years from date of creation or last effective date (whichever is later)
- **Recommended:** 7 years to align with statute of limitations

**Implementation:**

**AWS CloudWatch:**
```bash
aws logs put-retention-policy \
  --log-group-name /aws/orthanc/oauth \
  --retention-in-days 2555  # ~7 years
```

**Azure Monitor:**
```bash
az monitor log-analytics workspace table update \
  --resource-group myResourceGroup \
  --workspace-name myWorkspace \
  --name OrthancOAuth_CL \
  --retention-time 2555
```

**GCP Cloud Logging:**
```bash
gcloud logging sinks create orthanc-oauth-archive \
  --log-filter='resource.type="gce_instance" AND jsonPayload.event_type=~".*"' \
  --destination=storage.googleapis.com/orthanc-audit-archive \
  --storage-bucket-retention-days=2555
```

## Log Monitoring and Alerting

### Critical Alerts (Immediate Response)

**Multiple Failed Authentication Attempts:**
```
Query: event_type = "AUTHENTICATION_FAILED"
Threshold: > 5 failures from same IP in 5 minutes
Alert: Page on-call security team
```

**Unauthorized Access Attempt:**
```
Query: event_type = "AUTHORIZATION_FAILED"
Threshold: > 3 attempts from same user in 1 hour
Alert: Email security team
```

**Configuration Error:**
```
Query: event_type = "CONFIGURATION_ERROR"
Threshold: Any occurrence
Alert: Page on-call admin
```

### Warning Alerts (Business Hours Response)

**Elevated Rate Limiting:**
```
Query: event_type = "RATE_LIMIT_EXCEEDED"
Threshold: > 10 occurrences in 1 hour
Alert: Email operations team
```

**High Cache Miss Rate:**
```
Query: cache_miss_rate > 20%
Threshold: Sustained for > 15 minutes
Alert: Email operations team
```

### Example Alert Configurations

**CloudWatch Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name orthanc-failed-auth \
  --alarm-description "Multiple failed authentication attempts" \
  --metric-name FailedAuthentications \
  --namespace Orthanc/OAuth \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:security-alerts
```

**Azure Alert Rule:**
```bash
az monitor metrics alert create \
  --name orthanc-failed-auth \
  --resource-group myResourceGroup \
  --scopes /subscriptions/.../resourceGroups/.../providers/Microsoft.Compute/virtualMachines/orthanc-vm \
  --condition "count OrthancOAuth_CL | where event_type_s == 'AUTHENTICATION_FAILED' > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action security-alerts
```

## Log Review Procedures

### Weekly Review (Security Team)

**Objective:** Identify suspicious patterns and policy violations.

**Tasks:**
1. Review failed authentication attempts
2. Review authorization failures
3. Review rate limiting events
4. Verify no configuration errors
5. Check for unusual access patterns
6. Document findings

**Report Template:**
```markdown
# Weekly Audit Log Review - Week of YYYY-MM-DD

## Summary
- Total events: X
- Failed authentications: X (Y% change from last week)
- Authorization failures: X
- Rate limit triggers: X

## Findings
- [Finding 1]: Description and remediation
- [Finding 2]: Description and remediation

## Action Items
- [ ] Action 1 (Owner: Name, Due: Date)
- [ ] Action 2 (Owner: Name, Due: Date)

## Reviewed By: [Name]
## Date: [Date]
```

### Monthly Review (Privacy Officer)

**Objective:** Ensure compliance with HIPAA audit requirements.

**Tasks:**
1. Verify log retention is configured correctly
2. Verify all required events are being logged
3. Review access patterns for appropriateness
4. Identify any emergency access usage
5. Validate log integrity (no gaps, tampering)
6. Document review

### Quarterly Review (Management)

**Objective:** Strategic security posture assessment.

**Tasks:**
1. Review trends over quarter
2. Assess security control effectiveness
3. Identify areas for improvement
4. Update security policies if needed
5. Present to leadership

## Log Analysis Queries

### Common Investigation Queries

**Find All Access by Specific User:**
```sql
SELECT timestamp, event_type, action, resource, result
FROM audit_logs
WHERE user_id = 'user@example.com'
  AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
```

**Identify Unusual Access Times:**
```sql
SELECT user_id, COUNT(*) as access_count,
       MIN(HOUR(timestamp)) as earliest_hour,
       MAX(HOUR(timestamp)) as latest_hour
FROM audit_logs
WHERE event_type IN ('TOKEN_ACQUIRED', 'DATA_ACCESS')
  AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY user_id
HAVING earliest_hour < 6 OR latest_hour > 22
```

**Find Failed Access from Same IP:**
```sql
SELECT source_ip, COUNT(*) as failure_count,
       COUNT(DISTINCT user_id) as unique_users
FROM audit_logs
WHERE event_type IN ('AUTHENTICATION_FAILED', 'AUTHORIZATION_FAILED')
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY source_ip
HAVING failure_count > 10
ORDER BY failure_count DESC
```

**Detect Potential Data Exfiltration:**
```sql
SELECT user_id, source_ip,
       COUNT(*) as study_access_count,
       COUNT(DISTINCT resource) as unique_studies
FROM audit_logs
WHERE event_type = 'DATA_ACCESS'
  AND action = 'retrieve'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY user_id, source_ip
HAVING study_access_count > 100
```

## Security Best Practices

### 1. Protect Audit Logs

**Prevent Tampering:**
- ✅ Use append-only storage (S3 Object Lock, Azure Immutable Storage)
- ✅ Ship logs to centralized SIEM immediately
- ✅ Enable log file integrity monitoring
- ✅ Restrict access to logs (separate IAM role)

**Prevent Deletion:**
- ✅ Enable MFA delete on S3 buckets
- ✅ Use retention locks
- ✅ Backup logs to separate account/subscription
- ✅ Enable CloudTrail/Activity Log for log operations

### 2. Redact Sensitive Data

**Automatically redact:**
- OAuth client secrets
- Token values (log only token ID)
- Passwords
- Patient identifiers (if in error messages)
- Credit card numbers
- SSNs

**Configuration:**
```json
{
  "OAuth": {
    "AuditLogging": {
      "RedactSensitiveData": true,
      "RedactPatterns": [
        "(?i)(client_secret|password)\\s*[=:]\\s*[^\\s]+",
        "\\d{3}-\\d{2}-\\d{4}",  // SSN
        "\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}"  // Credit card
      ]
    }
  }
}
```

### 3. Monitor Log Volume

Track log volume for anomalies:

- Sudden spike: Possible attack or misconfiguration
- Sudden drop: Logging failure or service outage
- Gradual increase: Normal growth or investigate

### 4. Correlate Events

Use `correlation_id` to trace full request lifecycle:

```
correlation_id: req-abc123
  [15:30:00.100] TOKEN_ACQUIRED (SUCCESS)
  [15:30:00.150] CACHE_SET (SUCCESS)
  [15:30:00.200] DATA_ACCESS (SUCCESS)
```

### 5. Integrate with SIEM

**Recommended SIEM Solutions:**
- Splunk
- ELK Stack (Elasticsearch, Logstash, Kibana)
- AWS Security Hub + GuardDuty
- Azure Sentinel
- Google Chronicle

**Benefits:**
- Centralized log aggregation
- Automated correlation and analysis
- Pre-built compliance dashboards
- Automated alerting
- Threat intelligence integration

## Troubleshooting

### Logs Not Appearing

**Check:**
1. Logging enabled in configuration
2. Correct log destination configured
3. Sufficient IAM permissions
4. Network connectivity to log destination
5. Service is running

**Verify:**
```bash
# Check log configuration
curl http://localhost:8042/plugins/oauth/config | jq '.AuditLogging'

# Test log destination connectivity
aws logs describe-log-streams --log-group-name /aws/orthanc/oauth

# Check plugin logs for errors
tail -f /var/log/orthanc/plugins.log | grep -i "audit"
```

### High Log Volume / Cost

**Optimization:**
1. Reduce log level (INFO instead of DEBUG)
2. Filter out noisy events (health checks)
3. Sample high-volume events
4. Compress logs
5. Use cheaper storage tier for old logs

**Example Filter:**
```json
{
  "OAuth": {
    "AuditLogging": {
      "Filters": {
        "ExcludeEventTypes": ["HEALTH_CHECK"],
        "ExcludeUserAgents": ["ELB-HealthChecker/*"],
        "SampleRate": {
          "CACHE_HIT": 0.1  // Log only 10% of cache hits
        }
      }
    }
  }
}
```

## Compliance Checklist

- [ ] Audit logging enabled
- [ ] All required events logged
- [ ] User identity included in logs
- [ ] Timestamps in UTC with microsecond precision
- [ ] Log retention configured (6-7 years)
- [ ] Logs protected from tampering (append-only)
- [ ] Logs protected from deletion (retention lock)
- [ ] Access to logs restricted (separate IAM role)
- [ ] Logs shipped to centralized SIEM
- [ ] Automated alerting configured
- [ ] Weekly log review process documented
- [ ] Log review documented and signed
- [ ] Incident response plan references logs
- [ ] Disaster recovery includes log backups

## References

- [HIPAA Security Rule § 164.312(b)](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html)
- [NIST SP 800-92: Guide to Computer Security Log Management](https://csrc.nist.gov/publications/detail/sp/800-92/final)
- [NIST SP 800-53: AU (Audit and Accountability) Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [CIS Critical Security Controls: 8.2 - Audit Log Management](https://www.cisecurity.org/controls/)
