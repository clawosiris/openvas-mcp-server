# Usage

## First contact

Ask the model to run `openvas_test_connection`. It verifies, in order:
gateway liveness (`GET /health`), the gvmd/GMP version, and an
authenticated session round-trip. Each failure mode produces a distinct,
actionable message (gateway down vs. bad credentials vs. gvmd unreachable).

## Toolsets and gating

`gvm-mcp --list-toolsets` prints every toolset. Selection examples:

```bash
gvm-mcp                                     # default: everything except identity
gvm-mcp --read-only                         # reads only (48 tools)
gvm-mcp --toolsets targets,tasks,reports    # scoped surface
gvm-mcp --toolsets default,identity         # opt into user administration
```

`--read-only` removes every mutating tool from the router — clients do not
even see them in `tools/list`. The `system` toolset (connection test,
version) is always present.

## Filters and pagination

Every list tool accepts:

- `filter` — a GMP filter expression, e.g. `name~web and severity>5`
- `filter_id` — UUID of a saved filter
- `page` / `per_page` — 1-indexed pagination (default 25, max 1000)

List tools return summarized rows plus a pagination envelope; use the
matching `openvas_get_*` tool for the full record.

## Typical scan flow

1. `openvas_create_target` — hosts, port list, optional credentials
2. `openvas_list_scan_configs` / `openvas_list_scanners` — pick UUIDs
3. `openvas_create_task` — bind target + config + scanner
4. `openvas_start_task` — returns the report UUID for the run
5. `openvas_get_task` — status/progress until `Done`
6. `openvas_get_report_results` — findings, filterable

## Report exports

```text
openvas_export_report        (report format UUID, or omit for native JSON)
        │  job id, status: queued
        ▼
openvas_get_job              (poll until status: succeeded)
        │
        ▼
openvas_download_job_result  (JSON inline; PDF/CSV/XML as base64 ≤ 3 MB)
```

Jobs and artifacts expire ~15 minutes after completion; `openvas_cancel_job`
aborts a running export. For artifacts larger than 3 MB, export with a
narrower `filter` or use the JSON format and page through results instead.

## Deletion semantics

Delete tools move resources to gvmd's trashcan by default; pass
`ultimate: true` for permanent deletion. Deleting a resource that is still
referenced (e.g. a target used by a task) surfaces the gateway's 409 with
the reason.
