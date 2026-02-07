# Resilience Patterns

This plugin supports advanced resilience patterns to handle failures gracefully.

## Circuit Breaker

The circuit breaker pattern prevents cascading failures by "opening" the circuit after a threshold of failures.

### Configuration

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "Url": "https://dicom.example.com",
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "${CLIENT_ID}",
        "ClientSecret": "${CLIENT_SECRET}",
        "ResilienceConfig": {
          "CircuitBreakerEnabled": true,
          "CircuitBreakerFailureThreshold": 5,
          "CircuitBreakerTimeout": 60
        }
      }
    }
  }
}
```

### Parameters

- `CircuitBreakerEnabled` (boolean, default: false): Enable circuit breaker
- `CircuitBreakerFailureThreshold` (integer, default: 5): Number of failures before opening circuit
- `CircuitBreakerTimeout` (number, default: 60): Seconds before attempting to close circuit

### States

- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Circuit is open, requests fail fast without calling service
- **HALF_OPEN**: Testing if service recovered, one request allowed

## Retry Strategies

Configure automatic retries with various backoff strategies.

### Configuration

```json
{
  "ResilienceConfig": {
    "RetryMaxAttempts": 3,
    "RetryStrategy": "exponential",
    "RetryInitialDelay": 1.0,
    "RetryMultiplier": 2.0,
    "RetryMaxDelay": 30.0
  }
}
```

### Strategies

#### Fixed Backoff
Constant delay between retries.

```json
{
  "RetryStrategy": "fixed",
  "RetryInitialDelay": 2.0
}
```

#### Linear Backoff
Linear increase in delay.

```json
{
  "RetryStrategy": "linear",
  "RetryInitialDelay": 1.0,
  "RetryIncrement": 1.0
}
```

#### Exponential Backoff (Recommended)
Exponential increase with optional maximum.

```json
{
  "RetryStrategy": "exponential",
  "RetryInitialDelay": 1.0,
  "RetryMultiplier": 2.0,
  "RetryMaxDelay": 30.0
}
```

## Best Practices

1. **Enable circuit breaker in production** to prevent cascading failures
2. **Use exponential backoff** for retry strategy
3. **Set reasonable timeouts** (60s circuit breaker, 30s max retry delay)
4. **Monitor metrics** to tune thresholds
