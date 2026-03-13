# Phase 5: Testing

**Duration:** Ongoing  
**Status:** Planning

---

## Overview

Testing strategy with >80% coverage target.

---

## 5.1 Unit Tests

### Full Coverage

| Component | Tests |
|-----------|-------|
| `config.py` | All config scenarios |
| `client/base.py` | Connection, retry, thread safety |
| `client/local.py` | Socket connection |
| `client/remote.py` | TLS connection, SSL context |
| `errors.py` | All error types |
| `validators.py` | All validation functions |

### Edge Cases Only

| Component | Focus |
|-----------|-------|
| Services | Invalid inputs, error handling |
| MCP toolsets | Error responses |
| CLI commands | Error display |

---

## 5.2 Mocking Strategy

```python
# Mock client for service tests
@pytest.fixture
def mock_client():
    client = MagicMock(spec=GvmClient)
    return client

# Mock GMP for client tests
@pytest.fixture  
def mock_gmp():
    gmp = MagicMock(spec=Gmp)
    gmp.is_connected.return_value = True
    return gmp
```

---

## 5.3 Integration Tests

### Docker Compose Setup

```yaml
services:
  gvmd:
    image: greenbone/gvmd
    ports:
      - "9390:9390"
    
  vulnerable-target:
    image: vulnerables/web-dvwa
```

### Test Scenarios

- [ ] Full lifecycle: create target → run scan → get report
- [ ] Concurrent requests
- [ ] Connection failure recovery
- [ ] Large report handling

---

## 5.4 CI Pipeline

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov=src
```

---

## Deliverables

- [ ] Unit tests (>80% coverage)
- [ ] Integration test suite
- [ ] CI/CD pipeline
- [ ] Coverage reporting
