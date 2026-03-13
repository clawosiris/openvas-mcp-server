# CLI Installation

## Requirements

- Python 3.11+
- Access to GVM daemon (gvmd)

## Install via pip

```bash
pip install openvas-mcp
```

## Install from source

```bash
git clone https://github.com/clawosiris/openvas-mcp-server.git
cd openvas-mcp-server
pip install .
```

## Verify installation

```bash
openvas --version
```

## First-time setup

Run the interactive configuration:

```bash
openvas configure
```

This will prompt for:
- Connection type (local/remote)
- Socket path or hostname
- GVM credentials
- Timeout settings

Configuration is saved to `~/.config/openvas-mcp/config.toml`.

## Test connection

```bash
openvas test
```
