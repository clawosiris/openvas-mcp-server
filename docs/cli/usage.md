# CLI Usage

## Overview

```bash
openvas [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version |
| `--json` | Output as JSON |
| `--help` | Show help |

## Commands

### Configuration

```bash
# Interactive setup
openvas configure

# Show current config
openvas configure --show

# Reset configuration
openvas configure --reset

# Test connection
openvas test
```

### System

```bash
# Show GVM version and status
openvas system version

# Show feed status
openvas system feeds
```

---

## Command Reference

*Commands will be added as services are implemented.*

### Target Commands

```bash
# List targets
openvas target list [--filter FILTER]

# Get target details
openvas target get <TARGET_ID>

# Create target
openvas target create --name NAME --host HOST [--host HOST...]

# Delete target
openvas target delete <TARGET_ID> [--force]
```

### Scan Commands

```bash
# List scans/tasks
openvas scan list

# Start scan
openvas scan start <TASK_ID>

# Stop scan
openvas scan stop <TASK_ID>

# Show scan status
openvas scan status <TASK_ID>
```

### Report Commands

```bash
# List reports
openvas report list [--task TASK_ID]

# Show report summary
openvas report summary <REPORT_ID>

# Export report
openvas report export <REPORT_ID> --format pdf -o report.pdf
```

---

## Output Formats

### Table (default)

```bash
openvas target list
```

### JSON

```bash
openvas target list --json
```

### Quiet (script-friendly)

```bash
openvas target create --name "Test" --host 1.2.3.4 -q
# Outputs only the ID
```
