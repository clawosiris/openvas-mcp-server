# End-to-End Tests

Integration tests that run against a live GVM/OpenVAS instance.

## Requirements

- Running gvmd (Greenbone Vulnerability Manager Daemon)
- Access via Unix socket or TLS
- Valid credentials

## Setup

### Docker Compose (Recommended)

```bash
# Start GVM stack
docker compose -f docker/gvm-stack.yml up -d

# Wait for initialization (~5 minutes first time)
docker compose -f docker/gvm-stack.yml logs -f gvmd
```

### Environment Variables

```bash
export GVM_STYLE=local
export GVM_SOCKET_PATH=/run/gvmd/gvmd.sock
export GVM_USERNAME=admin
export GVM_PASSWORD=admin
```

Or for remote:

```bash
export GVM_STYLE=remote
export GVM_HOSTNAME=gvm.example.com
export GVM_PORT=9390
export GVM_USERNAME=admin
export GVM_PASSWORD=secret
```

## Running Tests

```bash
# Run e2e tests only
poetry run pytest tests/e2e -v

# Run with specific markers
poetry run pytest tests/e2e -v -m "slow"

# Skip e2e in CI (default)
poetry run pytest --ignore=tests/e2e
```

## Test Structure

```
e2e/
├── conftest.py          # Fixtures (live GVM connection)
├── test_targets.py      # Target CRUD lifecycle
├── test_scans.py        # Scan create → start → poll → report
├── test_reports.py      # Report retrieval and export
└── test_cli.py          # CLI command smoke tests
```

## Writing E2E Tests

```python
import pytest
from src.infrastructure import ConfigLoader, create_client

@pytest.fixture
def gvm_client():
    """Live GVM client - requires running gvmd."""
    config = ConfigLoader.from_env_and_file()
    return create_client(config)

def test_list_targets(gvm_client):
    """Verify we can list targets from live GVM."""
    from src.services.targets import TargetService
    
    service = TargetService(gvm_client)
    result = service.list()
    
    assert result is not None
    # May be empty, but should not error
```

## CI Integration

E2E tests are excluded from CI by default. To run in CI:

1. Set up GVM service container
2. Configure secrets for `GVM_PASSWORD`
3. Add workflow step:

```yaml
- name: Run E2E tests
  env:
    GVM_STYLE: local
    GVM_SOCKET_PATH: /run/gvmd/gvmd.sock
    GVM_USERNAME: admin
    GVM_PASSWORD: ${{ secrets.GVM_PASSWORD }}
  run: poetry run pytest tests/e2e -v
```

## Notes

- E2E tests are slower (~seconds per test)
- Some tests create real resources (targets, scans)
- Tests should clean up after themselves
- Use unique names with timestamps to avoid conflicts
