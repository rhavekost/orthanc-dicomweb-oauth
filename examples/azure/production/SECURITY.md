# Security Best Practices

This document outlines the security features and best practices for the production deployment.

## Network Security

### VNet Isolation
- All backend services deployed in private subnets
- No direct internet access to PostgreSQL, Storage, or Container Registry
- Container Apps Environment integrated with VNet

### Private Endpoints
- **PostgreSQL**: Accessible only via `10.0.2.x` private IP
- **Storage Account**: Blob service accessible via `10.0.3.x` private IP
- **Container Registry**: Registry service accessible via `10.0.3.x` private IP
- **DNS**: Automatic resolution via Private DNS zones

### Network Security Groups (Future Enhancement)
- Apply NSGs to restrict traffic between subnets
- Allow only necessary ports and protocols

## Identity and Access Management

### Managed Identity
- **System-Assigned**: Container App has automatic managed identity
- **No Secrets**: No client credentials stored or managed
- **Automatic Rotation**: Azure handles credential rotation

### RBAC Assignments
- **Least Privilege**: Only required roles assigned
- **DICOM Data Owner**: For DICOM Service read/write
- **Storage Blob Data Contributor**: For blob storage access
- **AcrPull**: For pulling container images only

### Secret Management
- **Orthanc Password**: Stored as Container App secret
- **PostgreSQL Password**: Stored as Container App secret
- **Auto-Generated**: Passwords generated during deployment

## Data Protection

### Encryption at Rest
- Storage Account: Microsoft-managed keys
- PostgreSQL: Microsoft-managed keys
- Container Registry: Microsoft-managed keys

### Encryption in Transit
- TLS 1.2+ enforced on all services
- HTTPS only for Container App ingress
- PostgreSQL requires SSL connections

### Data Retention
- Blob Storage: 7-day soft delete enabled
- PostgreSQL: Point-in-time restore supported (7 days)
- Logs: Retained in Log Analytics (30 days default)

## Monitoring and Auditing

### Logging
- Container App logs to Log Analytics
- PostgreSQL logs to Log Analytics
- Storage Account diagnostic logs enabled

### Metrics
- Prometheus metrics exposed by Orthanc plugin
- Azure Monitor metrics for all services

### Alerts (Future Enhancement)
- Failed authentication attempts
- Unusual network traffic patterns
- Resource utilization thresholds

## Compliance

### HIPAA Compliance Considerations
- Enable audit logging for all services
- Implement data loss prevention policies
- Regular access reviews
- Encrypt data at rest and in transit
- Business Associate Agreement (BAA) with Azure

### Data Residency
- All data stays in selected Azure region
- No cross-region replication by default
- Consider geo-redundancy for HA

## Hardening Checklist

- [ ] Enable Azure Defender for all services
- [ ] Configure Network Security Groups
- [ ] Enable firewall rules on Storage Account
- [ ] Enable AAD authentication for PostgreSQL
- [ ] Rotate Orthanc admin password regularly
- [ ] Review and minimize RBAC assignments
- [ ] Enable diagnostic logging for all resources
- [ ] Configure alert rules for security events
- [ ] Implement backup and disaster recovery
- [ ] Regular security assessments

## Vulnerability Management

### Container Image Scanning
- Enable Azure Defender for Container Registry
- Scan images before deployment
- Regular base image updates

### Dependency Management
- Keep Python dependencies updated
- Monitor for security advisories
- Use Dependabot or similar tools

### Patch Management
- Container Apps: Automatic platform updates
- PostgreSQL: Managed service handles patching
- Application: Regular image rebuilds

## Incident Response

### Security Event Detection
1. Monitor Container App logs for authentication failures
2. Check Azure Activity Log for unauthorized changes
3. Review Network Watcher logs for suspicious traffic

### Response Procedures
1. Isolate affected resources
2. Rotate credentials if compromised
3. Review and revoke RBAC assignments if needed
4. Analyze logs to determine scope
5. Document and report incident

## References

- [Azure Security Best Practices](https://learn.microsoft.com/azure/security/fundamentals/best-practices-and-patterns)
- [Container Apps Security](https://learn.microsoft.com/azure/container-apps/security)
- [HIPAA on Azure](https://learn.microsoft.com/azure/compliance/offerings/offering-hipaa-us)
