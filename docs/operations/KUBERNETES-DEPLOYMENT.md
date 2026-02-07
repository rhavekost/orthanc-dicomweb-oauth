# Kubernetes Deployment Guide

This guide provides best practices and examples for deploying Orthanc with OAuth plugin on Kubernetes.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Ingress Controller                      │
│                    (NGINX/Traefik/ALB)                      │
└────────────┬─────────────────────────────┬──────────────────┘
             │                              │
    ┌────────▼────────┐           ┌────────▼────────┐
    │   Orthanc Pod   │           │   Orthanc Pod   │
    │   + OAuth Plugin│           │   + OAuth Plugin│
    └────────┬────────┘           └────────┬────────┘
             │                              │
             └──────────────┬───────────────┘
                            │
                     ┌──────▼──────┐
                     │    Redis    │
                     │  StatefulSet │
                     └─────────────┘
```

## Prerequisites

- Kubernetes cluster 1.24+
- kubectl configured
- Helm 3.0+ (for Helm deployment)
- Container registry access

## Deployment Methods

### Method 1: Helm Chart (Recommended)

**Install:**
```bash
helm install orthanc-oauth ./kubernetes/helm \
  --set oauth.clientId="your-client-id" \
  --set oauth.clientSecret="your-client-secret" \
  --set redis.enabled=true
```

**Upgrade:**
```bash
helm upgrade orthanc-oauth ./kubernetes/helm \
  --set image.tag="2.0.1"
```

**Uninstall:**
```bash
helm uninstall orthanc-oauth
```

### Method 2: Plain Kubernetes Manifests

```bash
kubectl apply -f kubernetes/examples/basic-deployment.yaml
kubectl apply -f kubernetes/examples/redis-deployment.yaml
```

## Configuration

### Values Configuration (Helm)

See `kubernetes/helm/values.yaml` for all options:

```yaml
# Key configuration options
replicaCount: 3

image:
  repository: your-registry/orthanc-oauth
  tag: "2.0.0"
  pullPolicy: IfNotPresent

oauth:
  enabled: true
  clientId: "your-client-id"
  clientSecret: "your-client-secret"
  tokenEndpoint: "https://login.microsoftonline.com/.../oauth2/v2.0/token"

redis:
  enabled: true
  host: "redis-master"
  port: 6379

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

### Health Checks

**Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /app/explorer.html
    port: 8042
  initialDelaySeconds: 30
  periodSeconds: 10
```

**Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /plugins/oauth/status
    port: 8042
  initialDelaySeconds: 10
  periodSeconds: 5
```

**Startup Probe:**
```yaml
startupProbe:
  httpGet:
    path: /app/explorer.html
    port: 8042
  failureThreshold: 30
  periodSeconds: 10
```

## Horizontal Pod Autoscaling (HPA)

**Based on CPU:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orthanc-oauth-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orthanc-oauth
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Resource Limits

**Recommended Resources:**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

**Production Recommendations:**
- Start with requests: 512Mi memory, 250m CPU
- Monitor actual usage for 1 week
- Adjust based on 95th percentile usage
- Set limits at 2x requests for headroom

## Storage

**Volume for Orthanc Database:**
```yaml
volumeClaimTemplates:
  - metadata:
      name: orthanc-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "fast-ssd"
      resources:
        requests:
          storage: 100Gi
```

**Volume Types by Cloud Provider:**
- **AWS:** gp3 (general purpose SSD)
- **Azure:** Premium_LRS (premium SSD)
- **GCP:** pd-ssd (SSD persistent disk)

## Networking

### Ingress Configuration

**NGINX Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orthanc-oauth-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "0"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - orthanc.example.com
    secretName: orthanc-tls
  rules:
  - host: orthanc.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: orthanc-oauth
            port:
              number: 8042
```

### Service Configuration

**ClusterIP (Internal Only):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: orthanc-oauth
spec:
  type: ClusterIP
  ports:
  - port: 8042
    targetPort: 8042
    protocol: TCP
  selector:
    app: orthanc-oauth
```

## Security

### Pod Security Context

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

### Container Security

```yaml
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orthanc-oauth-netpol
spec:
  podSelector:
    matchLabels:
      app: orthanc-oauth
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8042
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # OAuth provider
```

## Redis Configuration

### Redis StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

### Redis High Availability

For production, use Redis Sentinel or Redis Cluster:

```bash
# Using Bitnami Redis Helm chart
helm install redis bitnami/redis \
  --set architecture=replication \
  --set auth.password=your-redis-password
```

## Monitoring

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: orthanc-oauth
spec:
  selector:
    matchLabels:
      app: orthanc-oauth
  endpoints:
  - port: metrics
    path: /plugins/oauth/metrics
    interval: 30s
```

### Key Metrics to Monitor

```promql
# Cache hit rate
rate(orthanc_oauth_cache_hits_total[5m]) /
  rate(orthanc_oauth_cache_requests_total[5m])

# Token acquisition rate
rate(orthanc_oauth_token_acquisitions_total[5m])

# Error rate
rate(orthanc_oauth_errors_total[5m])

# Request latency
histogram_quantile(0.95,
  rate(orthanc_oauth_request_duration_seconds_bucket[5m]))
```

## Deployment Strategies

### Rolling Update (Default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### Blue/Green Deployment

1. Deploy new version with different label
2. Test new version
3. Update Service selector to new version
4. Scale down old version

### Canary Deployment

1. Deploy canary with small replica count
2. Monitor metrics
3. Gradually increase canary replicas
4. Replace all replicas when confident

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app=orthanc-oauth
kubectl describe pod orthanc-oauth-xxx
kubectl logs orthanc-oauth-xxx
```

### Check OAuth Status

```bash
kubectl exec orthanc-oauth-xxx -- curl localhost:8042/plugins/oauth/status
```

### Check Redis Connection

```bash
kubectl exec orthanc-oauth-xxx -- redis-cli -h redis -p 6379 ping
```

### Common Issues

**Problem: Pods not starting**
- Check image pull secrets
- Verify resource limits
- Review pod events

**Problem: OAuth failures**
- Verify client credentials in secrets
- Check network policies allow OAuth provider access
- Review OAuth provider logs

**Problem: Cache misses**
- Verify Redis connectivity
- Check Redis service DNS resolution
- Review cache configuration

## Best Practices

1. **Use Helm for Complex Deployments:** Easier to manage and upgrade
2. **Enable HPA:** Auto-scale based on load
3. **Use Redis for Multi-Replica:** Share tokens across pods
4. **Set Resource Limits:** Prevent resource exhaustion
5. **Configure Health Checks:** Enable self-healing
6. **Use Network Policies:** Restrict pod-to-pod communication
7. **Enable TLS:** Encrypt ingress traffic
8. **Monitor Metrics:** Track cache hits, errors, latency
9. **Use Secrets for Credentials:** Never hardcode in configs
10. **Test Disaster Recovery:** Practice failure scenarios

## Cloud-Specific Guides

### AWS EKS

```bash
# Use AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds"

# Use EBS CSI driver for storage
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable"
```

### Azure AKS

```bash
# Use Azure Disk for storage
storageClassName: managed-premium
```

### Google GKE

```bash
# Use GCE Persistent Disk
storageClassName: pd-ssd
```

## Migration from Docker Compose

1. Convert docker-compose.yml to Kubernetes manifests
2. Create ConfigMaps for configuration files
3. Create Secrets for sensitive data
4. Deploy to staging cluster
5. Test thoroughly
6. Deploy to production

See `kubernetes/examples/` for sample manifests.

## Related Documentation

- [Distributed Caching](DISTRIBUTED-CACHING.md)
- [Backup and Recovery](BACKUP-RECOVERY.md)
- [Monitoring and Metrics](../monitoring/METRICS.md)
- [Security Best Practices](../security/BEST-PRACTICES.md)

## Support

For questions or issues with Kubernetes deployments:
- GitHub Issues: https://github.com/rhavekost/orthanc-dicomweb-oauth/issues
- Documentation: https://orthanc-dicomweb-oauth.readthedocs.io
