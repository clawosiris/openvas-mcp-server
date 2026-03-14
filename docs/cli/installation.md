# CLI Installation

## Prerequisites

- [Greenbone Community Edition](https://greenbone.github.io/docs/latest/) containers installed and running
- Docker and Docker Compose

## Setup

### 1. Copy the Docker Compose Override

Copy the override file from this repository into your Greenbone Community Edition directory:

```bash
cp docker-compose.override.yml /path/to/greenbone-community-container/
```

### 2. Set Credentials (Optional)

If your GVM credentials differ from the default (`admin`/`admin`), create or edit a `.env` file in your Greenbone CE directory:

```env
GVM_USERNAME=admin
GVM_PASSWORD=your-password-here
```

### 3. Start the CLI Container

```bash
cd /path/to/greenbone-community-container
docker compose up -d openvas-cli
```

### 4. Test Connection

```bash
docker exec greenbone-community-edition-openvas-cli-1 openvas system test
```

### 5. Set Up Shell Alias

To avoid typing the full `docker exec` command every time, add an alias to your shell.

#### macOS / Linux (zsh)

Add to `~/.zshrc`:

```bash
alias openvas='docker exec -it greenbone-community-edition-openvas-cli-1 openvas'
```

Reload:

```bash
source ~/.zshrc
```

#### macOS / Linux (bash)

Add to `~/.bashrc`:

```bash
alias openvas='docker exec -it greenbone-community-edition-openvas-cli-1 openvas'
```

Reload:

```bash
source ~/.bashrc
```

#### Windows (PowerShell)

Add to your PowerShell profile (`$PROFILE`):

```powershell
function openvas { docker exec -it greenbone-community-edition-openvas-cli-1 openvas $args }
```

Reload:

```powershell
. $PROFILE
```

#### Windows (Command Prompt)

Create a file `openvas.bat` in a directory on your `PATH`:

```batch
@echo off
docker exec -it greenbone-community-edition-openvas-cli-1 openvas %*
```

### 6. Verify

```bash
openvas system version
openvas system test
```

## Docker Image

The CLI runs in its own container (`ghcr.io/clawosiris/openvas-cli`), separate from the MCP server. Start only the services you need:

```bash
docker compose up -d openvas-cli              # CLI only
docker compose up -d openvas-mcp              # MCP server only
docker compose up -d openvas-mcp openvas-cli  # Both
```

## Usage

Once the alias is set up, use the CLI as documented in the [Usage Guide](usage.md):

```bash
openvas target list
openvas task list
openvas report list
```

> **Note:** Environment variables (`GVM_USERNAME`, `GVM_PASSWORD`, etc.) are already configured inside the container via the Docker Compose override. No need to pass them through the alias.
