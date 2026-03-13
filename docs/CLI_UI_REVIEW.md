# CLI UI Interactions — Review Document

**Status:** Draft for Review  
**Delete after approval**

---

## 1. First Run / Configuration

```
$ openvas

  ╭─────────────────────────────────────────╮
  │     OpenVAS MCP CLI - First Setup       │
  ╰─────────────────────────────────────────╯

  No configuration found. Let's set it up.

  Connection type [local/remote]: local
  Socket path [/run/gvmd/gvmd.sock]: 
  
  GMP username [admin]: admin
  GMP password: ••••••••
  
  Timeout (seconds) [60]: 60
  Retry attempts [3]: 3

  Testing connection... ✓ Connected (GVM 22.4)

  Save configuration? [Y/n]: y
  ✓ Saved to ~/.config/openvas-mcp/config.toml

  Run 'openvas --help' to see available commands.
```

---

## 2. Help / Commands

```
$ openvas --help

  Usage: openvas [OPTIONS] COMMAND [ARGS]...

  OpenVAS/GVM command-line interface.

  ╭─ Options ───────────────────────────────╮
  │ --version      Show version             │
  │ --json         Output as JSON           │
  │ --help         Show this message        │
  ╰─────────────────────────────────────────╯

  ╭─ Commands ──────────────────────────────╮
  │ configure   Configure GVM connection    │
  │ test        Test connection             │
  │ target      Target management           │
  │ scan        Scan/Task management        │
  │ report      Report management           │
  │ vuln        Vulnerability queries       │
  │ note        Note management             │
  │ override    Override management         │
  │ alert       Alert management            │
  │ credential  Credential management       │
  │ schedule    Schedule management         │
  │ policy      Policy management           │
  │ audit       Audit management            │
  │ ticket      Ticket management           │
  │ asset       Asset management            │
  │ config      Scan config management      │
  │ system      System information          │
  ╰─────────────────────────────────────────╯
```

```
$ openvas target --help

  Usage: openvas target [OPTIONS] COMMAND [ARGS]...

  Target management commands.

  ╭─ Commands ──────────────────────────────╮
  │ list     List targets                   │
  │ get      Get target details             │
  │ create   Create new target              │
  │ modify   Modify existing target         │
  │ delete   Delete target                  │
  │ clone    Clone target                   │
  ╰─────────────────────────────────────────╯
```

---

## 3. List Commands

### Table Output (default)

```
$ openvas target list

  ╭─ Targets (3 total) ─────────────────────────────────────────────────╮
  │ ID                                   │ Name          │ Hosts        │
  ├──────────────────────────────────────┼───────────────┼──────────────┤
  │ a1b2c3d4-e5f6-7890-abcd-ef1234567890 │ Web Servers   │ 192.168.1.10 │
  │ b2c3d4e5-f6a7-8901-bcde-f12345678901 │ DB Servers    │ 10.0.0.0/24  │
  │ c3d4e5f6-a7b8-9012-cdef-123456789012 │ DMZ           │ 5 hosts      │
  ╰──────────────────────────────────────┴───────────────┴──────────────╯
```

### JSON Output

```
$ openvas target list --json

{
  "count": 3,
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Web Servers",
      "hosts": ["192.168.1.10"],
      "in_use": true
    },
    ...
  ]
}
```

### Filtered

```
$ openvas target list --filter "name~Web"

  ╭─ Targets (1 total) ─────────────────────────────────────────────────╮
  │ ID                                   │ Name          │ Hosts        │
  ├──────────────────────────────────────┼───────────────┼──────────────┤
  │ a1b2c3d4-e5f6-7890-abcd-ef1234567890 │ Web Servers   │ 192.168.1.10 │
  ╰──────────────────────────────────────┴───────────────┴──────────────╯
```

---

## 4. Get Commands

```
$ openvas target get a1b2c3d4-e5f6-7890-abcd-ef1234567890

  ╭─ Target: Web Servers ───────────────────────────────────────────────╮
  │                                                                     │
  │  ID:          a1b2c3d4-e5f6-7890-abcd-ef1234567890                  │
  │  Name:        Web Servers                                           │
  │  Comment:     Production web server cluster                         │
  │  In Use:      Yes (2 tasks)                                         │
  │                                                                     │
  │  Hosts:       192.168.1.10                                          │
  │               192.168.1.11                                          │
  │               192.168.1.12                                          │
  │                                                                     │
  │  Exclude:     (none)                                                │
  │  Alive Test:  ICMP Ping                                             │
  │  Port List:   All IANA (default)                                    │
  │                                                                     │
  │  Credentials:                                                       │
  │    SSH:       ssh-prod-key                                          │
  │    SMB:       (none)                                                │
  │                                                                     │
  ╰─────────────────────────────────────────────────────────────────────╯
```

---

## 5. Create Commands

### With Arguments

```
$ openvas target create --name "New Target" --host 192.168.1.100 --host 192.168.1.101

  ✓ Created target: New Target
    ID: d4e5f6a7-b8c9-0123-def0-234567890123
```

### Interactive Mode

```
$ openvas target create

  ╭─ Create Target ─────────────────────────────────────────────────────╮
  
  Name: Production Servers
  Comment (optional): Main production environment
  
  Hosts (comma-separated or CIDR): 10.0.0.0/24
  Exclude hosts (optional): 10.0.0.1
  
  Alive test [ICMP Ping]: 
  Port list [All IANA]: 
  
  Add SSH credential? [y/N]: y
  Select credential:
    1. ssh-prod-key
    2. ssh-dev-key
    3. (create new)
  Choice [1]: 1
  
  ╰─────────────────────────────────────────────────────────────────────╯
  
  ✓ Created target: Production Servers
    ID: e5f6a7b8-c9d0-1234-ef01-345678901234
```

---

## 6. Modify Commands

```
$ openvas target modify a1b2c3d4-... --name "Web Servers v2" --add-host 192.168.1.13

  ✓ Modified target: Web Servers v2
```

---

## 7. Delete Commands

```
$ openvas target delete a1b2c3d4-e5f6-7890-abcd-ef1234567890

  Target: Web Servers
  
  ⚠ This target is used by 2 tasks:
    - Daily Scan
    - Weekly Full Scan
  
  Delete anyway? [y/N]: y
  
  ✓ Deleted target: Web Servers
```

### Force Delete

```
$ openvas target delete a1b2c3d4-... --force

  ✓ Deleted target: Web Servers
```

### Ultimate Delete (permanent)

```
$ openvas target delete a1b2c3d4-... --ultimate

  ⚠ WARNING: This will permanently delete the target.
    It cannot be restored from trash.
  
  Type 'DELETE' to confirm: DELETE
  
  ✓ Permanently deleted target: Web Servers
```

---

## 8. Scan/Task Operations

### Create and Start

```
$ openvas scan create --name "Quick Scan" --target a1b2c3d4-... --config "Full and fast"

  ✓ Created task: Quick Scan
    ID: f6a7b8c9-d0e1-2345-f012-456789012345

$ openvas scan start f6a7b8c9-...

  ✓ Started scan: Quick Scan
    Report ID: a7b8c9d0-e1f2-3456-0123-567890123456
```

### Status with Progress

```
$ openvas scan status f6a7b8c9-...

  ╭─ Scan: Quick Scan ──────────────────────────────────────────────────╮
  │                                                                     │
  │  Status:    Running                                                 │
  │  Progress:  ████████████░░░░░░░░  62%                              │
  │  Started:   2025-03-13 10:15:00                                     │
  │  Duration:  15m 32s                                                 │
  │                                                                     │
  │  Hosts:     3 total, 2 complete, 1 scanning                        │
  │  Results:   45 found (8 High, 12 Medium, 25 Low)                   │
  │                                                                     │
  ╰─────────────────────────────────────────────────────────────────────╯
```

### Watch Mode

```
$ openvas scan watch f6a7b8c9-...

  Watching scan: Quick Scan (Ctrl+C to stop)

  [10:15:32] Started
  [10:16:45] Host 192.168.1.10 complete (15 results)
  [10:18:20] Host 192.168.1.11 complete (18 results)
  [10:20:55] ████████████████████  100%
  [10:20:56] Scan complete

  Results: 45 total (8 High, 12 Medium, 25 Low)
  Report:  a7b8c9d0-e1f2-3456-0123-567890123456
```

---

## 9. Report Commands

### List Reports

```
$ openvas report list --task f6a7b8c9-...

  ╭─ Reports for: Quick Scan ───────────────────────────────────────────╮
  │ Date                │ Status    │ High │ Med  │ Low  │ Total       │
  ├─────────────────────┼───────────┼──────┼──────┼──────┼─────────────┤
  │ 2025-03-13 10:20    │ Done      │ 8    │ 12   │ 25   │ 45          │
  │ 2025-03-12 10:15    │ Done      │ 9    │ 11   │ 24   │ 44          │
  │ 2025-03-11 10:18    │ Done      │ 9    │ 12   │ 23   │ 44          │
  ╰─────────────────────┴───────────┴──────┴──────┴──────┴─────────────╯
```

### Report Summary

```
$ openvas report summary a7b8c9d0-...

  ╭─ Report Summary ────────────────────────────────────────────────────╮
  │                                                                     │
  │  Task:      Quick Scan                                              │
  │  Date:      2025-03-13 10:20:56                                     │
  │  Duration:  5m 56s                                                  │
  │                                                                     │
  │  ╭─ Severity Distribution ────────────────────────────────────────╮ │
  │  │  Critical  ████                              2                 │ │
  │  │  High      ████████                          8                 │ │
  │  │  Medium    ████████████                     12                 │ │
  │  │  Low       █████████████████████████        25                 │ │
  │  ╰────────────────────────────────────────────────────────────────╯ │
  │                                                                     │
  │  Hosts Scanned: 3                                                   │
  │  Total Results: 45                                                  │
  │                                                                     │
  ╰─────────────────────────────────────────────────────────────────────╯
```

### Export Report

```
$ openvas report export a7b8c9d0-... --format pdf -o report.pdf

  Exporting report... ████████████████████ 100%
  ✓ Saved to report.pdf (2.4 MB)
```

---

## 10. Error Display

### Resource Not Found

```
$ openvas target get invalid-uuid

  ✗ Error: Target not found

    The target 'invalid-uuid' does not exist or has been deleted.

    Hint: Use 'openvas target list' to see available targets.
```

### Validation Error

```
$ openvas target create --name "" --host 192.168.1.1

  ✗ Error: Invalid input

    • name: Field is required and cannot be empty
    
    Hint: Use 'openvas target create --help' for usage.
```

### Connection Error

```
$ openvas target list

  ✗ Error: Connection failed

    Cannot connect to GVM at /run/gvmd/gvmd.sock
    
    Possible causes:
    • gvmd service is not running
    • Socket path is incorrect
    • Permission denied
    
    Hint: Check 'systemctl status gvmd' and verify socket path.
```

### Resource In Use

```
$ openvas target delete a1b2c3d4-...

  ✗ Error: Cannot delete target

    Target 'Web Servers' is in use by 2 tasks:
    • Daily Scan (running)
    • Weekly Full Scan
    
    Hint: Stop running tasks first, or use --force to delete anyway.
```

---

## 11. System Commands

```
$ openvas system version

  ╭─ GVM System Info ───────────────────────────────────────────────────╮
  │                                                                     │
  │  GVM Version:     22.4.0                                            │
  │  GMP Version:     22.4                                              │
  │  Backend:         PostgreSQL                                        │
  │                                                                     │
  │  Feed Status:                                                       │
  │    NVT:           2025-03-13 (up to date)                          │
  │    SCAP:          2025-03-13 (up to date)                          │
  │    CERT:          2025-03-12 (1 day old)                           │
  │                                                                     │
  ╰─────────────────────────────────────────────────────────────────────╯
```

---

## 12. Configuration Management

```
$ openvas configure --show

  ╭─ Current Configuration ─────────────────────────────────────────────╮
  │                                                                     │
  │  Connection:  local                                                 │
  │  Socket:      /run/gvmd/gvmd.sock                                   │
  │  Username:    admin                                                 │
  │  Timeout:     60s                                                   │
  │  Retries:     3                                                     │
  │                                                                     │
  │  Config file: ~/.config/openvas-mcp/config.toml                     │
  │                                                                     │
  ╰─────────────────────────────────────────────────────────────────────╯
```

```
$ openvas configure --reset

  ⚠ This will delete your saved configuration.
  
  Continue? [y/N]: y
  
  ✓ Configuration reset. Run 'openvas configure' to set up again.
```

---

## 13. Quiet/Verbose Modes

### Quiet (script-friendly)

```
$ openvas target create --name "Test" --host 1.2.3.4 -q
d4e5f6a7-b8c9-0123-def0-234567890123

$ openvas scan start d4e5f6a7-... -q
report:a7b8c9d0-e1f2-3456-0123-567890123456
```

### Verbose

```
$ openvas target list -v

  [DEBUG] Loading config from ~/.config/openvas-mcp/config.toml
  [DEBUG] Connecting to /run/gvmd/gvmd.sock
  [DEBUG] Authenticating as 'admin'
  [DEBUG] Executing: get_targets(filter_string="rows=-1")
  [DEBUG] Response: 200 OK (3 targets, 45ms)
  
  ╭─ Targets (3 total) ...
```

---

## Design Notes

### Colors

| Element | Color |
|---------|-------|
| Success (✓) | Green |
| Error (✗) | Red |
| Warning (⚠) | Yellow |
| Info | Blue |
| Muted/hint | Dim/Gray |

### Icons

| Icon | Meaning |
|------|---------|
| ✓ | Success |
| ✗ | Error |
| ⚠ | Warning |
| → | Action/Flow |
| • | List item |

### Table Style

- Box drawing characters for borders
- Header row highlighted
- Alternating row colors (optional)
- Truncate long values with `...`

---

## Questions for Review

1. **Interactive vs Arguments:** Should all create/modify commands support both modes?

2. **Confirmation prompts:** Which destructive actions need confirmation?
   - Delete: Yes (with --force to skip)
   - Ultimate delete: Always confirm
   - Stop running scan: ?

3. **Progress display:** Use progress bar or spinner for long operations?

4. **Color scheme:** Any preferences for the color palette?

5. **Default output:** Table or JSON for list commands?
