# Phase 4: CLI

**Duration:** 3-4 days  
**Status:** Completed

---

## Overview

Typer-based CLI with interactive configuration.

---

## 4.1 CLI Structure

```
openvas
├── configure          # Interactive setup
├── test               # Test connection
├── target
│   ├── list
│   ├── get <id>
│   ├── create
│   └── delete <id>
├── scan
│   ├── list
│   ├── get <id>
│   ├── create
│   ├── start <id>
│   ├── stop <id>
│   └── delete <id>
├── report
│   ├── list
│   ├── get <id>
│   ├── summary <id>
│   └── export <id>
└── ...
```

---

## 4.2 Interactive Configuration

```
$ openvas configure

OpenVAS MCP - Connection Setup

Connection style [local/remote]: local
Socket path [/run/gvmd/gvmd.sock]: 
GMP username [admin]: 
GMP password: ****
Timeout (seconds) [60]: 

Save configuration? [Y/n]: y
Configuration saved to ~/.config/openvas-mcp/config.toml
```

---

## 4.3 Output Formats

```bash
# Table (default)
$ openvas target list

# JSON
$ openvas target list --json

# Specific fields
$ openvas target list --fields id,name,hosts
```

---

## 4.4 Command Examples

```bash
# Create target
$ openvas target create --name "Web Servers" --host 192.168.1.10 --host 192.168.1.11

# Start scan
$ openvas scan start abc-123-def

# Export report
$ openvas report export abc-123 --format pdf > report.pdf

# Check compliance
$ openvas compliance status --target abc-123
```

---

## 4.5 Error Output

```
$ openvas target get invalid-id

Error: Target not found: invalid-id

Hint: Use 'openvas target list' to see available targets.
```

---

## Deliverables

- [ ] Typer CLI structure
- [ ] All commands implemented
- [ ] Interactive configuration
- [ ] Table/JSON output formatting
- [ ] Error display with hints
