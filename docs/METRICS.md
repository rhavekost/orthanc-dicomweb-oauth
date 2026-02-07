# Prometheus Metrics

The plugin exposes Prometheus metrics for monitoring.

## Metrics Endpoint

```
GET /dicomweb-oauth/metrics
```

Returns metrics in Prometheus text format.

## Available Metrics

### Token Acquisition

```
dicomweb_oauth_token_acquisitions_total{server, status}
```
Total token acquisition attempts by status (success/failure).

```
dicomweb_oauth_token_acquisition_duration_seconds{server}
```
Histogram of token acquisition duration.

### Caching

```
dicomweb_oauth_cache_hits_total{server}
```
Total cache hits.

```
dicomweb_oauth_cache_misses_total{server}
```
Total cache misses.

### Circuit Breaker

```
dicomweb_oauth_circuit_breaker_state{server}
```
Current circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN).

```
dicomweb_oauth_circuit_breaker_rejections_total{server}
```
Total requests rejected by open circuit.

### Retries

```
dicomweb_oauth_retry_attempts_total{server}
```
Total retry attempts.

### HTTP Requests

```
dicomweb_oauth_http_requests_total{method, endpoint, status}
```
Total HTTP requests by method, endpoint, and status code.

```
dicomweb_oauth_http_request_duration_seconds{method, endpoint}
```
Histogram of HTTP request duration.

### Errors

```
dicomweb_oauth_errors_total{server, error_code, category}
```
Total errors by error code and category.

## Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'orthanc-dicomweb-oauth'
    static_configs:
      - targets: ['orthanc:8042']
    metrics_path: '/dicomweb-oauth/metrics'
    scrape_interval: 15s
```

## Grafana Dashboard

Example queries:

### Token Acquisition Success Rate
```promql
rate(dicomweb_oauth_token_acquisitions_total{status="success"}[5m])
/
rate(dicomweb_oauth_token_acquisitions_total[5m])
```

### Cache Hit Rate
```promql
rate(dicomweb_oauth_cache_hits_total[5m])
/
(rate(dicomweb_oauth_cache_hits_total[5m]) + rate(dicomweb_oauth_cache_misses_total[5m]))
```

### Circuit Breaker State
```promql
dicomweb_oauth_circuit_breaker_state
```

### P95 Token Acquisition Time
```promql
histogram_quantile(0.95, rate(dicomweb_oauth_token_acquisition_duration_seconds_bucket[5m]))
```
