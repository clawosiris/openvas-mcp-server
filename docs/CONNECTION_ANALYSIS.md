# Connection Management Deep Analysis

**Version:** 2025.03  
**Status:** Technical Analysis

---

## Executive Summary

This document analyzes connection management challenges for the OpenVAS MCP Server and proposes solutions for:
1. **Timeout handling** with retry mechanisms
2. **Concurrency model** to avoid bottlenecks
3. **Auto-reconnect** strategy

---

## 1. python-gvm Connection Behavior

### 1.1 Default Configuration

```python
DEFAULT_TIMEOUT = 60  # seconds

# UnixSocketConnection
UnixSocketConnection(
    path="/run/gvmd/gvmd.sock",
    timeout=60  # socket read/write timeout
)

# TLSConnection  
TLSConnection(
    hostname="gvm.example.com",
    port=9390,
    timeout=60
)
```

### 1.2 State Tracking

python-gvm tracks two separate states:

| State | Flag | Set When |
|-------|------|----------|
| Connection | `_connected` | After `connect()` succeeds |
| Authentication | `_authenticated` | After `authenticate()` succeeds |

**Critical:** These are independent. Connection can drop while `_authenticated` remains `True`.

### 1.3 Failure Modes

| Failure | Exception | Message Pattern |
|---------|-----------|-----------------|
| Socket not found | `GvmError` | "Socket {path} does not exist" |
| Connection refused | `GvmError` | "Could not connect to socket" |
| Server disconnect | `GvmError` | "Remote closed the connection" |
| Read timeout | `GvmError` | "Timeout while reading the response" |
| Auth failure | `GvmError` | "Authentication failed" (from GMP response) |

### 1.4 No Built-in Retry

```python
# python-gvm source analysis:
# - No 'retry' pattern in gmp module
# - No 'reconnect' pattern in protocol
# - WE MUST IMPLEMENT retry/reconnect ourselves
```

---

## 2. gvmd Server Characteristics

### 2.1 Single-Threaded GMP Processing

**⚠️ CRITICAL FINDING:**

```
gvmd processes GMP commands SEQUENTIALLY (single-threaded).
Even with multiple connections, operations are queued internally.
```

**Implications:**
- Connection pooling does NOT improve throughput to a single gvmd
- Parallel requests from MCP → serialized at gvmd anyway
- Our client-side lock mirrors gvmd's actual behavior

### 2.2 Session Persistence

gvmd sessions remain alive until:
1. Client disconnects explicitly
2. TCP connection drops (network failure)
3. gvmd restarts or crashes
4. OS-level TCP keepalive timeout (usually 2+ hours)
5. Firewall idle timeout (if remote connection)

**No configurable session timeout in gvmd itself.**

### 2.3 Long Operations

Some GMP operations are long-running:
- `get_reports` with full details: 30s - 5min+
- `get_results` on large scans: 10s - 2min+
- Scan start/stop: 1s - 30s

---

## 3. Concurrency Analysis

### 3.1 Current Design (Singleton + Lock)

```python
class GvmClient:
    _instance = None
    _operation_lock = threading.Lock()
    
    def execute(self, operation):
        with self._operation_lock:  # ← BOTTLENECK HERE
            return operation(self._gmp)
```

**Problem:** All operations serialized, even simple ones.

### 3.2 Why Connection Pooling Doesn't Help

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                               │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       │
│  │Req 1 │ │Req 2 │ │Req 3 │ │Req 4 │  (parallel requests)  │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘                       │
└─────┼────────┼────────┼────────┼────────────────────────────┘
      │        │        │        │
      ▼        ▼        ▼        ▼
┌─────────────────────────────────────────────────────────────┐
│                Connection Pool (4 conns)                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       │
│  │Conn 1│ │Conn 2│ │Conn 3│ │Conn 4│                       │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘                       │
└─────┼────────┼────────┼────────┼────────────────────────────┘
      │        │        │        │
      └────────┴────────┴────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    gvmd (SINGLE THREAD)                     │
│                                                             │
│    ┌─────┐ ← ┌─────┐ ← ┌─────┐ ← ┌─────┐                   │
│    │Req 1│   │Req 2│   │Req 3│   │Req 4│  (QUEUED!)        │
│    └─────┘   └─────┘   └─────┘   └─────┘                   │
│                                                             │
│    Processing: ████░░░░░░░░░░░░░░ (one at a time)          │
└─────────────────────────────────────────────────────────────┘

Result: 4 connections, still sequential execution.
Pool adds complexity without improving throughput.
```

### 3.3 Proposed Design: Connection per Request

For MCP (stdio transport), requests are naturally sequential.
For CLI, requests are naturally sequential.

**Recommendation:** Use connection-per-request with short-lived connections.

```python
class GvmClient:
    def __init__(self, config: GvmConfig):
        self._config = config
    
    def execute(self, operation: Callable[[Gmp], T]) -> T:
        """Create fresh connection for each operation."""
        with self._create_connection() as gmp:
            gmp.authenticate(...)
            return operation(gmp)
```

**Trade-offs:**

| Aspect | Singleton + Lock | Connection per Request |
|--------|------------------|------------------------|
| Connection overhead | 1 connect + 1 auth | N connects + N auths |
| Memory | Single socket | Socket per request |
| Complexity | Lock management | Simpler code |
| Failure isolation | One failure affects all | Isolated failures |
| Bottleneck | Client-side lock | None (gvmd handles) |

### 3.4 Hybrid Approach (Recommended)

```python
class GvmClient:
    """Lazy connection with automatic cleanup."""
    
    def __init__(self, config: GvmConfig):
        self._config = config
        self._gmp: Optional[Gmp] = None
        self._last_used: float = 0
        self._lock = threading.Lock()
    def execute(self, operation: Callable[[Gmp], T]) -> T:
        with self._lock:
            self._ensure_connection()
            try:
                result = operation(self._gmp)
                self._last_used = time.time()
                return result
            except GvmError as e:
                self._handle_error(e)
                raise
    
    def _ensure_connection(self):
        """Connect if needed."""
        if self._gmp is None or not self._gmp.is_connected():
            self._connect_with_retry()
    
    def _disconnect(self):
        """Clean disconnect."""
        if self._gmp:
            try:
                self._gmp.disconnect()
            except Exception:
                pass
            self._gmp = None
```

---

## 4. Retry Mechanism

### 4.1 Retry Strategy

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    
    # Retryable errors
    retryable_errors: tuple = (
        "Remote closed the connection",
        "Timeout while reading",
        "Connection refused",
        "Connection reset",
    )
```

### 4.2 Implementation

```python
def execute_with_retry(
    self, 
    operation: Callable[[Gmp], T],
    retry_config: RetryConfig = None
) -> T:
    """Execute with retry on error."""
    config = retry_config or self._default_retry_config
    last_error = None
    
    for attempt in range(config.max_attempts):
        try:
            return self._execute_single(operation)
        except GvmError as e:
            last_error = e
            
            if not self._is_retryable(e, config):
                raise  # Don't retry non-retryable errors
            
            if attempt < config.max_attempts - 1:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying..."
                )
                self._reconnect()  # Force reconnection
    
    raise last_error

def _is_retryable(self, error: GvmError, config: RetryConfig) -> bool:
    """Check if error should trigger retry."""
    error_msg = str(error).lower()
    return any(
        pattern.lower() in error_msg 
        for pattern in config.retryable_errors
    )
```

### 4.3 Non-Retryable Errors

These should fail immediately:
- Authentication failures
- Permission denied
- Invalid parameters
- Resource not found

```python
NON_RETRYABLE_PATTERNS = [
    "authentication failed",
    "permission denied",
    "invalid",
    "not found",
    "already exists",
]
```

---

## 5. Auto-Reconnect Strategy

### 5.1 When to Reconnect

| Trigger | Action |
|---------|--------|
| `is_connected() == False` | Reconnect before operation |
| `GvmError: Remote closed` | Reconnect and retry |
| `GvmError: Timeout` | Reconnect and retry |
| Auth failure after reconnect | Raise error (don't loop) |

### 5.2 Reconnect Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    execute(operation)                       │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │     is_connected()?         │
                    └─────────────┬───────────────┘
                           │             │
                          Yes           No
                           │             │
                           │             ▼
                           │    ┌─────────────────┐
                           │    │    connect()    │
                           │    └────────┬────────┘
                           │             │
                           │             ▼
                           │    ┌─────────────────┐
                           │    │  authenticate() │
                           │    └────────┬────────┘
                           │             │
                           ▼             ▼
                    ┌─────────────────────────────┐
                    │      run operation(gmp)     │
                    └─────────────┬───────────────┘
                           │             │
                        Success       Error
                           │             │
                           ▼             ▼
                    ┌──────────┐  ┌─────────────────┐
                    │  return  │  │   retryable?    │
                    └──────────┘  └────────┬────────┘
                                    │           │
                                   Yes          No
                                    │           │
                                    ▼           ▼
                            ┌───────────┐ ┌─────────┐
                            │  backoff  │ │  raise  │
                            │  reconnect│ │  error  │
                            │  retry    │ └─────────┘
                            └───────────┘
```

### 5.3 Circuit Breaker (Optional)

For repeated failures, implement circuit breaker:

```python
class CircuitBreaker:
    """Prevent retry storms on persistent failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        
        # half-open: allow one request to test
        return True
```

---

## 6. Recommended Architecture

### 6.1 Final Design

```python
class GvmClient:
    """
    GVM client with:
    - Lazy connection (connect on first use)
    - Automatic reconnection on failure
    - Exponential backoff retry
    - Idle connection cleanup
    - Circuit breaker for failure protection
    """
    
    def __init__(self, config: GvmConfig):
        self._config = config
        self._gmp: Optional[Gmp] = None
        self._lock = threading.RLock()  # Reentrant for nested calls
        self._last_used = 0.0
        self._retry_config = RetryConfig()
        self._circuit_breaker = CircuitBreaker()
        
        # Configuration

        self._operation_timeout = config.timeout or 300
    
    def execute(
        self, 
        operation: Callable[[Gmp], T],
        timeout: Optional[float] = None,
    ) -> T:
        """Execute operation with full resilience."""
        
        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            raise GvmUnavailableError(
                "GVM connection circuit breaker is open. "
                "Too many recent failures."
            )
        
        with self._lock:
            try:
                result = self._execute_with_retry(operation, timeout)
                self._circuit_breaker.record_success()
                return result
            except GvmError as e:
                self._circuit_breaker.record_failure()
                raise
```

### 6.2 Configuration Options

```python
@dataclass
class GvmConfig:
    # Connection
    connection_type: str = "tls"
    host: Optional[str] = None
    port: int = 9390
    socket_path: Optional[str] = None
    
    # Timeouts
    connection_timeout: int = 30      # Initial connection
    operation_timeout: int = 300      # Per-operation

    
    # Retry
    retry_max_attempts: int = 3
    
    # Circuit breaker
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 60.0
```

---

## 7. Performance Considerations

### 7.1 Lock Granularity

**Current:** Single lock for all operations ❌

**Better:** Operation-level timeout with lock

```python
def execute(self, operation, timeout=None):
    timeout = timeout or self._operation_timeout
    
    # Try to acquire lock with timeout
    acquired = self._lock.acquire(timeout=timeout)
    if not acquired:
        raise GvmTimeoutError(
            "Timeout waiting for GVM connection. "
            "Another operation is in progress."
        )
    
    try:
        return self._execute_with_retry(operation)
    finally:
        self._lock.release()
```

### 7.2 Connection Overhead Analysis

| Operation | Time (local socket) | Time (remote TLS) |
|-----------|--------------------:|------------------:|
| Connect | ~5ms | ~50-200ms |
| Authenticate | ~10ms | ~50-100ms |
| Simple query | ~20ms | ~100-300ms |
| **Total per-request** | ~35ms | ~200-600ms |

For MCP (sequential requests), this overhead is acceptable.

### 7.3 When to Consider Connection Pooling

Only if:
- Multiple gvmd instances (load balancing)
- Very high request volume (>100 req/sec)
- Latency-critical operations

For typical MCP/CLI usage: **NOT NEEDED**.

---

## 8. Summary

### Key Decisions

| Concern | Decision | Rationale |
|---------|----------|-----------|
| Concurrency model | Single connection + lock | gvmd is single-threaded anyway |
| Retry mechanism | Exponential backoff (3 attempts) | Handles transient failures |
| Reconnect trigger | On error | Handles failures |
| Lock timeout | Operation timeout | Prevent indefinite blocking |
| Circuit breaker | Optional, 5 failures | Prevent retry storms |

### Next Steps

1. Update ARCHITECTURE.md with these decisions
2. Implement `GvmClient` with retry/reconnect
3. Add configuration options for timeouts
4. Write tests for failure scenarios
