# CLI Usage

## Overview

```bash
openvas [OPTIONS] COMMAND [ARGS]...
```

## Commands

### System

```bash
openvas system version
openvas system test
```

### Target Commands

```bash
openvas target list [--filter FILTER]
openvas target get <TARGET_ID>
openvas target create --name NAME --host HOST [--host HOST...]
openvas target delete <TARGET_ID> [--force]
```

### Task (Scan) Commands

```bash
openvas task list [--filter FILTER]
openvas task get <TASK_ID>
openvas task create --name NAME --target TARGET_ID --config CONFIG_ID [--scanner SCANNER_ID]
openvas task start <TASK_ID>
openvas task stop <TASK_ID>
openvas task resume <TASK_ID>
openvas task clone <TASK_ID>
openvas task delete <TASK_ID> [--force] [--ultimate]
```

### Report Commands

```bash
openvas report list [--filter FILTER]
openvas report get <REPORT_ID>
openvas report detail <REPORT_ID> [--min-qod 70]
openvas report export <REPORT_ID> --format pdf -o report.pdf
openvas report delete <REPORT_ID> [--force]
```

### Utility Commands

```bash
# Scan configs
openvas scan-config list
openvas scan-config get <CONFIG_ID>

# Port lists
openvas port-list list
openvas port-list get <PORT_LIST_ID>

# Schedules
openvas schedule list
openvas schedule get <SCHEDULE_ID>
```

### Vulnerability Commands

```bash
openvas vuln list --report <REPORT_ID> [--min-qod 70]
openvas vuln search-nvts <QUERY>
```

## Output Formats

```bash
# JSON
openvas target list --json

# Quiet (script-friendly)
openvas target create --name "Test" --host 1.2.3.4 -q
```
