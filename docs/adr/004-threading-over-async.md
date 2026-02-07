# ADR 004: Threading Over Async/Await

**Status:** Accepted
**Date:** 2025-01 (retroactive documentation)
**Decision Makers:** Initial Project Team

## Context

The plugin needs thread-safe token caching to support concurrent HTTP requests from Orthanc. Python offers two main concurrency models:

1. **Threading with locks** (chosen)
2. **Async/await with asyncio**

Orthanc's Python plugin API is synchronous and uses native threads for concurrent request handling.

## Decision

Use **threading.Lock()** for token cache synchronization instead of async/await.

## Rationale

### Orthanc Constraints

1. **Synchronous Plugin API**
   - Orthanc's Python plugin API is fully synchronous
   - Callbacks like `OutgoingHttpFilter` are blocking
   - No async support in orthanc Python module

2. **Native Thread Pool**
   - Orthanc uses native threads for HTTP request handling
   - Multiple requests processed concurrently
   - Each request runs in separate thread

3. **Blocking I/O Expected**
   - HTTP token requests are blocking
   - requests library is synchronous
   - Orthanc expects synchronous behavior

### Why Threading?

1. **Direct Compatibility**
   ```python
   # Works seamlessly with Orthanc
   def OutgoingHttpFilter(method, uri, ip, username, headers):
       token = token_manager.get_token()  # Thread-safe
       headers["Authorization"] = f"Bearer {token}"
   ```

2. **Simple Mental Model**
   - One lock protects token cache
   - Threads block if token refresh in progress
   - No event loop management

3. **Proven Pattern**
   - Standard for concurrent access to shared state
   - Well-understood by Python developers
   - Minimal cognitive overhead

### Why NOT Async/Await?

1. **Incompatible with Orthanc API**
   ```python
   # Cannot do this - Orthanc callbacks aren't async
   async def OutgoingHttpFilter(method, uri, ...):  # ❌
       token = await token_manager.get_token()
   ```

2. **Would Require Full Rewrite**
   - All Orthanc callbacks would need wrapper functions
   - Run event loop in separate thread
   - Bridge between sync and async worlds
   - Significantly more complex

3. **No Performance Benefit**
   - Token acquisition is rare (once per hour typically)
   - HTTP requests are blocking anyway (requests library)
   - No I/O multiplexing needed

4. **Additional Dependencies**
   - Would need aiohttp instead of requests
   - More dependencies = larger attack surface
   - Async requests libraries less mature

## Implementation

### Thread-Safe Token Cache

```python
class TokenManager:
    def __init__(self, ...):
        self._lock = threading.Lock()
        self._token = None
        self._expires_at = None

    def get_token(self) -> str:
        """Thread-safe token retrieval with automatic refresh."""
        with self._lock:
            if self._is_token_valid():
                return self._token
            return self._acquire_token()
```

### Lock Scope

- **Lock acquired**: During token validation and acquisition
- **Lock released**: After token cached
- **Lock-free**: Token is copied to caller (immutable string)

### Performance Characteristics

- **Happy path (token valid)**: Lock held for microseconds
- **Refresh path (token expired)**: Lock held for ~500ms (HTTP request time)
- **Concurrent requests**: Block until refresh completes, then proceed

## Alternatives Considered

### Alternative 1: Async/Await

**Pros:**
- More modern Python idiom
- Better for high-concurrency scenarios
- Non-blocking I/O

**Cons:**
- ❌ Incompatible with Orthanc's synchronous API
- ❌ Requires event loop management
- ❌ Needs sync-async bridge
- ❌ More complex debugging
- ❌ Additional dependencies

**Decision:** Rejected due to Orthanc incompatibility

### Alternative 2: No Synchronization

**Pros:**
- Simplest implementation
- No lock overhead

**Cons:**
- ❌ Race conditions in token refresh
- ❌ Possible multiple token acquisitions
- ❌ Unsafe

**Decision:** Rejected - correctness over simplicity

### Alternative 3: Lock-Free Data Structures

**Pros:**
- Better performance under contention
- No blocking

**Cons:**
- ❌ Complex implementation
- ❌ Harder to verify correctness
- ❌ Overkill for token caching

**Decision:** Rejected - simple lock is sufficient

### Alternative 4: Process-Level Cache

**Pros:**
- Shared across plugin restarts
- Could survive Orthanc restarts

**Cons:**
- ❌ Adds filesystem/Redis dependency
- ❌ More complex
- ❌ Security risk (tokens on disk)
- ❌ Not needed (tokens expire anyway)

**Decision:** Rejected - memory cache sufficient

## Consequences

### Positive
- ✅ Simple, proven concurrency model
- ✅ No async complexity
- ✅ Works seamlessly with Orthanc
- ✅ Easy to test and debug
- ✅ Minimal dependencies

### Negative
- ❌ Threads block during token refresh (~500ms)
- ❌ Not "modern" async Python
- ❌ Lock contention possible under extreme load

### Mitigation

For the negative consequences:

1. **Blocking during refresh**
   - Rare (once per hour)
   - Refresh happens before expiration (buffer time)
   - Total block time < 1 second

2. **Lock contention**
   - Token reads are fast (microseconds)
   - Refresh is rare
   - Not a bottleneck in practice

## Performance Analysis

### Typical Load

- **Token reads**: 100 req/sec
- **Lock hold time**: 2 µs per read
- **Lock utilization**: 0.02%

### During Refresh

- **Refresh frequency**: Once per hour
- **Lock hold time**: 500 ms
- **Blocked requests**: ~50 (at 100 req/sec)
- **Recovery time**: Immediate after refresh

### Worst Case

- **Sustained 1000 req/sec**
- **Lock contention**: Still < 1%
- **Not a bottleneck**

## Testing Strategy

```python
def test_concurrent_token_access():
    """Multiple threads should safely access token."""
    token_manager = TokenManager(...)

    def access_token():
        return token_manager.get_token()

    # 100 concurrent threads
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(access_token) for _ in range(100)]
        tokens = [f.result() for f in futures]

    # All threads should get same token
    assert len(set(tokens)) == 1
```

## Future Considerations

If Orthanc ever supports async plugins:

1. Keep threading version as default
2. Add optional async implementation
3. Auto-detect plugin API version
4. Use async only if available

For now, threading is the right choice.

## Review Date

This decision should be reviewed if:
- Orthanc adds async plugin API
- Python introduces better concurrency primitives
- Lock contention becomes measurable bottleneck

## References

- [Python threading.Lock documentation](https://docs.python.org/3/library/threading.html#lock-objects)
- [Real Python: Threading vs Async](https://realpython.com/python-async-features/)
- [Orthanc Plugin Python API](https://orthanc.uclouvain.be/book/plugins/python.html)
