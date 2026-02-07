# Distributed Caching for Multi-Instance Deployments

This guide explains how to configure distributed caching to enable token sharing across multiple instances of the Orthanc OAuth plugin.

## Overview

When running multiple Orthanc instances behind a load balancer, each instance maintains its own token cache by default. This means:
- Each instance acquires tokens independently
- Higher load on OAuth provider
- Potential rate limiting issues
- Unnecessary network overhead

Distributed caching solves this by sharing tokens across all instances.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Orthanc    │     │  Orthanc    │     │  Orthanc    │
│  Instance 1 │     │  Instance 2 │     │  Instance 3 │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │   (Cache)   │
                    └─────────────┘
```

## Configuration

### Option 1: Redis (Recommended)

**Installation:**
```bash
# Install Redis dependency
pip install redis>=5.0.0

# Or add to requirements.txt
echo "redis>=5.0.0" >> requirements.txt
```

**Configuration in orthanc.json:**
```json
{
  "Plugins": ["/path/to/dicomweb_oauth_plugin.py"],
  "DicomWeb": {
    "OAuth": {
      "Enabled": true,
      "CacheBackend": "redis",
      "Redis": {
        "Host": "redis.example.com",
        "Port": 6379,
        "DB": 0,
        "Password": "${REDIS_PASSWORD}",
        "Prefix": "orthanc:oauth:"
      },
      "Servers": [...]
    }
  }
}
```

**Environment Variables:**
```bash
export REDIS_PASSWORD="your-redis-password"
```

### Option 2: Memory Cache (Default)

For single-instance deployments, the default in-memory cache is sufficient:

```json
{
  "DicomWeb": {
    "OAuth": {
      "Enabled": true,
      "CacheBackend": "memory"
    }
  }
}
```

## Deployment Patterns

### AWS ElastiCache Redis

```json
{
  "Redis": {
    "Host": "my-cluster.abc123.0001.use1.cache.amazonaws.com",
    "Port": 6379,
    "DB": 0,
    "Password": "${AWS_REDIS_PASSWORD}"
  }
}
```

### Azure Cache for Redis

```json
{
  "Redis": {
    "Host": "my-cache.redis.cache.windows.net",
    "Port": 6380,
    "DB": 0,
    "Password": "${AZURE_REDIS_KEY}",
    "SSL": true
  }
}
```

### Google Cloud Memorystore

```json
{
  "Redis": {
    "Host": "10.0.0.3",
    "Port": 6379,
    "DB": 0
  }
}
```

## Performance Considerations

**Cache Hit Rates:**
- Expected: 95-99% cache hit rate
- Token lifetime: Typically 3600s (1 hour)
- Cache TTL: Token lifetime - 60s (safety buffer)

**Scalability:**
- Redis can handle 100,000+ operations/second
- Typical plugin load: 10-100 cache operations/second
- Plenty of headroom for scaling

**Failover:**
- If Redis is unavailable, plugin falls back to direct token acquisition
- Temporary performance degradation, but no functionality loss
- Monitor Redis health in production

## Monitoring

**Key Metrics:**
```
orthanc_oauth_cache_hits_total
orthanc_oauth_cache_misses_total
orthanc_oauth_cache_errors_total
orthanc_oauth_token_acquisitions_total
```

**Healthy Ratios:**
- Cache hit rate: >95%
- Cache error rate: <0.1%

## Troubleshooting

**Problem: Cache misses too high**
- Check Redis connectivity
- Verify TTL configuration
- Check clock synchronization across instances

**Problem: Redis connection failures**
- Verify network connectivity
- Check Redis auth credentials
- Review firewall rules
- Check Redis service status

**Problem: Tokens not shared between instances**
- Verify all instances use same Redis configuration
- Check key prefix matches across instances
- Verify Redis DB number is consistent

## Security Considerations

1. **Encryption in Transit:** Use TLS for Redis connections in production
2. **Authentication:** Always set Redis password
3. **Network Isolation:** Run Redis in private subnet
4. **Key Expiration:** Tokens auto-expire based on OAuth provider TTL
5. **Namespace Isolation:** Use unique prefix per environment

## Migration from Memory to Redis

1. Deploy Redis instance
2. Update configuration with Redis settings
3. Restart Orthanc instances (rolling restart recommended)
4. Monitor cache hit rates
5. Verify token sharing across instances

No data migration needed - cache will populate naturally.

## Python Integration Example

For custom integrations or testing:

```python
from src.cache import RedisCache, MemoryCache
from src.token_manager import TokenManager

# Single instance deployment (default)
cache = MemoryCache()
manager = TokenManager("server1", config, cache=cache)

# Multi-instance deployment with Redis
cache = RedisCache(
    host="redis.example.com",
    port=6379,
    password="secret",
    prefix="orthanc:oauth:"
)
manager = TokenManager("server1", config, cache=cache)

# Tokens are automatically shared across all instances
# using the same Redis instance
```

## Cache Backend Interface

All cache backends implement the same interface:

```python
from src.cache import CacheBackend

class CacheBackend(ABC):
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    def delete(self, key: str) -> bool: ...
    def exists(self, key: str) -> bool: ...
    def clear(self) -> bool: ...
```

## Best Practices

1. **Use Redis for production** multi-instance deployments
2. **Set appropriate TTLs** - default is token lifetime - 60s
3. **Monitor cache metrics** - track hit rates and errors
4. **Use TLS** for Redis connections in production
5. **Isolate with key prefixes** - use different prefixes per environment
6. **Plan for failures** - Redis unavailability should not break functionality
7. **Test failover** - verify plugin works when Redis is down

## Related Documentation

- [Token Manager Architecture](../architecture/TOKEN-MANAGER.md)
- [OAuth Provider Configuration](../configuration/OAUTH-PROVIDERS.md)
- [Monitoring and Metrics](MONITORING.md)
- [Backup and Recovery](BACKUP-RECOVERY.md)

## Support

For questions or issues with distributed caching:
- GitHub Issues: https://github.com/rhavekost/orthanc-dicomweb-oauth/issues
- Email: support@example.com
