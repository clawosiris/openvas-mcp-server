# MCP Usage

## Overview

The OpenVAS MCP server exposes GVM functionality as tools that AI agents can use.

## Tool Reference

*Tools will be added as services are implemented.*

### Target Tools

| Tool | Description |
|------|-------------|
| `openvas_list_targets` | List all scan targets |
| `openvas_get_target` | Get target details by ID |
| `openvas_create_target` | Create a new scan target |
| `openvas_delete_target` | Delete a target |

### Scan Tools

| Tool | Description |
|------|-------------|
| `openvas_list_tasks` | List all scan tasks |
| `openvas_get_task` | Get task details |
| `openvas_create_task` | Create a new scan task |
| `openvas_start_task` | Start a scan |
| `openvas_stop_task` | Stop a running scan |

### Report Tools

| Tool | Description |
|------|-------------|
| `openvas_list_reports` | List reports |
| `openvas_get_report` | Get report details |
| `openvas_get_report_summary` | Get report summary |

### System Tools

| Tool | Description |
|------|-------------|
| `openvas_get_version` | Get GVM version info |
| `openvas_get_feeds` | Get feed status |

---

## Example Prompts

### List Targets

> "Show me all scan targets in OpenVAS"

### Create Target

> "Create a new scan target called 'Web Servers' with hosts 192.168.1.10 and 192.168.1.11"

### Run Scan

> "Start a vulnerability scan on the Web Servers target"

### Get Report

> "Show me the summary of the latest scan report"

---

## Error Handling

All tools return structured errors:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Target not found: abc-123",
    "details": {
      "resource_type": "target",
      "resource_id": "abc-123"
    }
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `NOT_FOUND` | Resource does not exist |
| `IN_USE` | Resource is in use |
| `INVALID_UUID` | Invalid ID format |
| `PERMISSION_DENIED` | Access denied |
| `CONNECTION_TIMEOUT` | GVM connection timeout |
| `GVM_INTERNAL` | GVM server error |
