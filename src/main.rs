use anyhow::Context;
use clap::Parser;
use rmcp::ServiceExt;
use rmcp::transport::stdio;
use tracing_subscriber::EnvFilter;

use gvm_mcp::config::{Cli, Config, Transport};
use gvm_mcp::mcp::GvmMcpServer;
use gvm_mcp::mcp::toolset::Toolset;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    if cli.list_toolsets {
        for toolset in Toolset::ALL {
            println!("{:<18} {}", toolset.name(), toolset.describe());
        }
        return Ok(());
    }

    // The stdio transport owns stdout for the MCP protocol; logs go to stderr.
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new(cli.log_level.clone())),
        )
        .with_writer(std::io::stderr)
        .with_ansi(false)
        .init();

    let config = Config::from_cli(cli)?;
    tracing::info!(
        gateway = %config.gateway_url,
        read_only = config.read_only,
        toolsets = %config.toolsets,
        "starting gvm-mcp"
    );

    match config.transport {
        Transport::Stdio => {
            let server = GvmMcpServer::new(config)?;
            let service = server
                .serve(stdio())
                .await
                .context("failed to start MCP server on stdio")?;
            service.waiting().await?;
        }
        Transport::StreamableHttp => {
            anyhow::bail!(
                "streamable-http transport is not implemented yet (roadmap phase 6); \
                 use --transport stdio"
            );
        }
    }

    Ok(())
}
