# Phase 3: MCP Server

**Duration:** 2-3 days  
**Status:** Completed

---

## Overview

FastMCP server exposing services as tools.

---

## 3.1 Server Setup

```python
# presentation/mcp/server.py
from mcp.server.fastmcp import FastMCP

def create_server() -> FastMCP:
    server = FastMCP(name="openvas-mcp")
    
    # Load config from environment
    config = load_config_from_env()
    client = create_client(config)
    
    # Register toolsets
    register_target_tools(server, TargetService(client))
    register_scan_tools(server, ScanService(client))
    register_report_tools(server, ReportService(client))
    # ...
    
    return server

def main():
    create_server().run(transport="stdio")
```

---

## 3.2 Tool Registration Pattern

```python
# presentation/mcp/toolsets/targets.py
def register_target_tools(server: FastMCP, service: TargetService):
    
    @server.tool()
    def list_targets(filter: str = "") -> dict:
        """List scan targets."""
        return service.list(filter).model_dump()
    
    @server.tool()
    def create_target(name: str, hosts: list[str]) -> dict:
        """Create a new scan target."""
        request = TargetCreateRequest(name=name, hosts=hosts)
        return service.create(request).model_dump()
```

---

## 3.3 Tool Categories

| Category | Tools | Count |
|----------|-------|-------|
| Target | list, get, create, delete | 4 |
| Scan | list, get, create, start, stop | 5 |
| Report | list, get, summary, export | 4 |
| Vulnerability | list, get, search_nvts | 3 |
| Note | list, get, create, update, delete | 5 |
| Override | list, get, create, update, delete | 5 |
| Compliance | list_policies, list_audits, start, stop, status | 5 |
| Ticket | list, get, create, update, delete | 5 |
| Asset | list_hosts, list_os, list_certs | 3 |
| System | version, status, configs, ports, creds | 5 |
| **Total** | | **~44** |

---

## 3.4 MCP Client Configuration

```json
{
  "mcpServers": {
    "openvas": {
      "command": "openvas-mcp",
      "env": {
        "GVM_STYLE": "local",
        "GVM_SOCKET_PATH": "/run/gvmd/gvmd.sock",
        "GVM_USERNAME": "admin",
        "GVM_PASSWORD": "secret"
      }
    }
  }
}
```

---

## 3.5 Error Responses

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

---

## Deliverables

- [ ] FastMCP server setup
- [ ] All tools registered (~44)
- [ ] Error handling for all tools
- [ ] Docker image
