//! CLI definition and runtime configuration.

use std::path::PathBuf;
use std::time::Duration;

use anyhow::{Context, bail};
use clap::{Parser, ValueEnum};
use secrecy::SecretString;
use url::Url;

use crate::mcp::toolset::ToolsetSelection;

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub enum Transport {
    Stdio,
    StreamableHttp,
}

#[derive(Debug, Parser)]
#[command(
    name = "gvm-mcp",
    version,
    about = "MCP server for Greenbone Vulnerability Management via the GVM REST gateway"
)]
pub struct Cli {
    /// Base URL of the rust-gvm-api REST gateway (origin, without /api/v1)
    #[arg(long, env = "GVM_GATEWAY_URL", default_value = "http://127.0.0.1:8080")]
    pub gateway_url: Url,

    /// gvmd username used to create gateway sessions
    #[arg(long, env = "GVM_USERNAME")]
    pub username: Option<String>,

    /// gvmd password (prefer --password-file / GVM_PASSWORD_FILE in production)
    #[arg(long, env = "GVM_PASSWORD", hide_env_values = true)]
    pub password: Option<String>,

    /// File containing the gvmd password (e.g. a mounted secret); takes
    /// precedence over --password / GVM_PASSWORD
    #[arg(long, env = "GVM_PASSWORD_FILE")]
    pub password_file: Option<PathBuf>,

    /// MCP transport
    #[arg(long, value_enum, env = "MCP_TRANSPORT", default_value_t = Transport::Stdio)]
    pub transport: Transport,

    /// Bind address for the streamable-http transport
    #[arg(long, env = "MCP_BIND_ADDR", default_value = "127.0.0.1:8000")]
    pub bind_addr: std::net::SocketAddr,

    /// Host headers accepted by the streamable-http transport (DNS-rebinding
    /// guard). Use "*" to disable the check behind a trusted reverse proxy.
    #[arg(
        long,
        env = "MCP_ALLOWED_HOSTS",
        value_delimiter = ',',
        default_value = "localhost,127.0.0.1,::1"
    )]
    pub allowed_hosts: Vec<String>,

    /// Require this bearer token on the streamable-http endpoint. When set,
    /// requests must carry `Authorization: Bearer <token>`. Unset means no
    /// inbound authentication (intended for stdio, or HTTP behind a trusted
    /// proxy that authenticates for you).
    #[arg(long, env = "MCP_AUTH_TOKEN", hide_env_values = true)]
    pub auth_token: Option<String>,

    /// Comma-separated toolsets to expose ("default", "all", or names from
    /// --list-toolsets). Identity is always opt-in.
    #[arg(long, env = "GVM_TOOLSETS", value_delimiter = ',')]
    pub toolsets: Vec<String>,

    /// Expose only read (non-mutating) tools
    #[arg(long, env = "GVM_READ_ONLY", default_value_t = false)]
    pub read_only: bool,

    /// HTTP timeout towards the gateway, in seconds
    #[arg(long, env = "GVM_HTTP_TIMEOUT", default_value_t = 30)]
    pub timeout_secs: u64,

    /// Log level when RUST_LOG is unset (error|warn|info|debug|trace)
    #[arg(long, env = "GVM_LOG_LEVEL", default_value = "info")]
    pub log_level: String,

    /// List available toolsets and exit
    #[arg(long, default_value_t = false)]
    pub list_toolsets: bool,
}

/// Validated runtime configuration derived from [`Cli`].
#[derive(Debug, Clone)]
pub struct Config {
    pub gateway_url: Url,
    pub username: String,
    pub password: SecretString,
    pub transport: Transport,
    pub bind_addr: std::net::SocketAddr,
    pub allowed_hosts: Vec<String>,
    pub auth_token: Option<SecretString>,
    pub toolsets: ToolsetSelection,
    pub read_only: bool,
    pub timeout: Duration,
}

impl Config {
    pub fn from_cli(cli: Cli) -> anyhow::Result<Self> {
        if !matches!(cli.gateway_url.scheme(), "http" | "https") {
            bail!(
                "gateway URL must use http or https, got '{}'",
                cli.gateway_url
            );
        }
        if cli.gateway_url.host_str().is_none() {
            bail!("gateway URL has no host: '{}'", cli.gateway_url);
        }

        let username = cli
            .username
            .filter(|u| !u.is_empty())
            .context("gvmd username is required (--username or GVM_USERNAME)")?;

        let password = match &cli.password_file {
            Some(path) => {
                let raw = std::fs::read_to_string(path).with_context(|| {
                    format!("failed to read password file '{}'", path.display())
                })?;
                let trimmed = raw.trim_end_matches(['\r', '\n']);
                if trimmed.is_empty() {
                    bail!("password file '{}' is empty", path.display());
                }
                trimmed.to_owned()
            }
            None => cli
                .password
                .filter(|p| !p.is_empty())
                .context("gvmd password is required (GVM_PASSWORD or --password-file)")?,
        };

        if cli.timeout_secs == 0 {
            bail!("--timeout-secs must be greater than 0");
        }

        let toolsets = ToolsetSelection::parse(&cli.toolsets)?;

        let auth_token = cli
            .auth_token
            .filter(|token| !token.is_empty())
            .map(SecretString::from);

        Ok(Self {
            gateway_url: cli.gateway_url,
            username,
            password: SecretString::from(password),
            transport: cli.transport,
            bind_addr: cli.bind_addr,
            allowed_hosts: cli.allowed_hosts,
            auth_token,
            toolsets,
            read_only: cli.read_only,
            timeout: Duration::from_secs(cli.timeout_secs),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn base_cli() -> Cli {
        Cli::parse_from([
            "gvm-mcp",
            "--gateway-url",
            "http://gateway.example:8080",
            "--username",
            "admin",
            "--password",
            "s3cret",
        ])
    }

    #[test]
    fn builds_config_from_flags() {
        let config = Config::from_cli(base_cli()).unwrap();
        assert_eq!(config.username, "admin");
        assert_eq!(config.gateway_url.as_str(), "http://gateway.example:8080/");
        assert_eq!(config.timeout, Duration::from_secs(30));
        assert!(!config.read_only);
    }

    #[test]
    fn rejects_missing_username() {
        let mut cli = base_cli();
        cli.username = None;
        let err = Config::from_cli(cli).unwrap_err();
        assert!(err.to_string().contains("username"));
    }

    #[test]
    fn rejects_missing_password() {
        let mut cli = base_cli();
        cli.password = None;
        let err = Config::from_cli(cli).unwrap_err();
        assert!(err.to_string().contains("password"));
    }

    #[test]
    fn rejects_non_http_scheme() {
        let mut cli = base_cli();
        cli.gateway_url = Url::parse("unix:/run/gvmd.sock").unwrap();
        let err = Config::from_cli(cli).unwrap_err();
        assert!(err.to_string().contains("http"));
    }

    #[test]
    fn password_file_takes_precedence() {
        let dir = std::env::temp_dir().join("gvm-mcp-test-config");
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("password");
        std::fs::write(&path, "from-file\n").unwrap();

        let mut cli = base_cli();
        cli.password_file = Some(path.clone());
        let config = Config::from_cli(cli).unwrap();
        use secrecy::ExposeSecret;
        assert_eq!(config.password.expose_secret(), "from-file");
        std::fs::remove_file(path).ok();
    }

    #[test]
    fn empty_password_file_is_rejected() {
        let dir = std::env::temp_dir().join("gvm-mcp-test-config");
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("empty-password");
        std::fs::write(&path, "\n").unwrap();

        let mut cli = base_cli();
        cli.password_file = Some(path.clone());
        let err = Config::from_cli(cli).unwrap_err();
        assert!(err.to_string().contains("empty"));
        std::fs::remove_file(path).ok();
    }
}
