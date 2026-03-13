# CLI Development

## Project Structure

```
src/openvas_mcp/presentation/cli/
├── __init__.py
├── main.py           # CLI entry point (Typer app)
├── config.py         # CLI configuration handling
└── commands/
    ├── __init__.py
    ├── configure.py  # Configuration commands
    ├── targets.py    # Target commands
    ├── tasks.py      # Task/scan commands
    └── ...
```

## Adding a New Command

1. Create command file in `commands/`:

```python
# commands/targets.py
import typer
from rich.console import Console

from openvas_mcp.services.targets import TargetService

app = typer.Typer(help="Target management")
console = Console()

@app.command("list")
def list_targets(
    filter: str = typer.Option("", "--filter", "-f"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List scan targets."""
    service = _get_service()
    result = service.list(filter)
    
    if json_output:
        console.print_json(result.model_dump_json())
    else:
        _print_table(result)
```

2. Register in `main.py`:

```python
from .commands import targets

app.add_typer(targets.app, name="target")
```

## Running Locally

```bash
# Install in dev mode
poetry install

# Run CLI
poetry run openvas --help
```

## Testing

```bash
# Run CLI tests
poetry run pytest tests/presentation/cli/
```
