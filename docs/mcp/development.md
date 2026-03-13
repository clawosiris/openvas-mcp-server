# MCP Development

## Project Structure

```
src/presentation/mcp/
├── __init__.py
├── server.py         # MCP server entry point
└── toolsets/
    ├── __init__.py
    ├── targets.py    # Target tools
    ├── tasks.py      # Task/scan tools
    └── ...
```

## Adding a New Tool

1. Create or update toolset in `toolsets/`:

```python
# toolsets/targets.py
from mcp.server.fastmcp import FastMCP

from services.targets import TargetService

def register_target_tools(server: FastMCP, service: TargetService):
    
    @server.tool(name="openvas_list_targets")
    def list_targets(filter: str = "") -> dict:
        """List all scan targets.
        
        Args:
            filter: Optional GMP filter string
            
        Returns:
            List of targets with id, name, hosts
        """
        result = service.list(filter)
        return result.model_dump()
    
    @server.tool(name="openvas_create_target")
    def create_target(name: str, hosts: list[str]) -> dict:
        """Create a new scan target.
        
        Args:
            name: Target name
            hosts: List of hosts (IP, CIDR, or hostname)
            
        Returns:
            Created target details
        """
        request = TargetCreateRequest(name=name, hosts=hosts)
        result = service.create(request)
        return result.model_dump()
```

2. Register in `server.py`:

```python
from .toolsets import targets

def create_server() -> FastMCP:
    server = FastMCP(name="openvas-mcp")
    
    client = create_client(config)
    targets.register_target_tools(server, TargetService(client))
    
    return server
```

## Running Locally

```bash
# Install in dev mode
poetry install

# Run MCP server (stdio)
poetry run openvas-mcp

# Test with MCP inspector
npx @anthropic/mcp-inspector poetry run openvas-mcp
```

## Testing

```bash
# Run MCP tests
poetry run pytest tests/presentation/mcp/
```

## Docker Build

```bash
docker build -t openvas-mcp .
docker run -e GVM_USERNAME=admin -e GVM_PASSWORD=secret openvas-mcp
```
