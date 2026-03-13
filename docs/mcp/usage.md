# MCP Usage

## Overview

The OpenVAS MCP server exposes GVM functionality as MCP tools.

## Tool Reference

### System

- `openvas_get_version`
- `openvas_test_connection`

### Targets

- `openvas_list_targets`
- `openvas_get_target`
- `openvas_create_target`
- `openvas_delete_target`

### Tasks (Scans)

- `openvas_list_tasks`
- `openvas_get_task`
- `openvas_create_task`
- `openvas_start_task`
- `openvas_stop_task`
- `openvas_resume_task`
- `openvas_delete_task`
- `openvas_clone_task`

### Reports

- `openvas_list_reports`
- `openvas_get_report`
- `openvas_get_report_detail`
- `openvas_get_report_summary`
- `openvas_export_report`
- `openvas_delete_report`

### Utility Services

- `openvas_list_scan_configs`
- `openvas_get_scan_config`
- `openvas_list_port_lists`
- `openvas_get_port_list`
- `openvas_list_schedules`
- `openvas_get_schedule`

### Vulnerabilities

- `openvas_list_vulnerabilities`
- `openvas_search_nvts`

## Example Prompts

- "Show me all scan targets in OpenVAS"
- "Create a target named 'Web Servers' with hosts 192.168.1.10 and 192.168.1.11"
- "Start task <uuid> and return the report id"
- "Export report <uuid> as PDF"
- "List vulnerabilities for report <uuid> with QoD >= 70"
