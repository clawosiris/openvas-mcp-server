# CLI Installation

## Prerequisites

- [Greenbone Community Edition](https://greenbone.github.io/docs/latest/) containers installed and running
- Docker and Docker Compose

## Setup

### 1. Add the Docker Compose Override

Create a `docker-compose.override.yml` in your Greenbone Community Edition directory with the CLI service:

```yaml
services:
  openvas-cli:
    image: ghcr.io/clawosiris/openvas-cli:latest
    entrypoint: []
    command: ["sleep", "infinity"]
    restart: on-failure
    environment:
      GVM_STYLE: local
      GVM_SOCKET_PATH: /run/gvmd/gvmd.sock
      GVM_USERNAME: ${GVM_USERNAME:?Set GVM_USERNAME in .env}
      GVM_PASSWORD: ${GVM_PASSWORD:?Set GVM_PASSWORD in .env}
      GVM_TIMEOUT: "60"
    volumes:
      - gvmd_socket_vol:/run/gvmd
    depends_on:
      gvmd:
        condition: service_started
```

Or copy the full override file (includes both MCP and CLI services) from this repository:

```bash
cp docker-compose.override.yml /path/to/greenbone-community-container/
```

### 2. Set Credentials

Create a `.env` file in your Greenbone CE directory with your GVM credentials:

```env
GVM_USERNAME=<your-username>
GVM_PASSWORD=<your-password>
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
