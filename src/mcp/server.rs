//! rmcp server wiring and the system toolset.

use std::sync::Arc;

use rmcp::handler::server::ServerHandler;
use rmcp::model::{CallToolResult, ContentBlock, Implementation, ServerCapabilities, ServerInfo};
use rmcp::{ErrorData as McpError, tool, tool_handler, tool_router};
use serde::Serialize;

use crate::config::Config;
use crate::gateway::GatewayClient;
use crate::gateway::models::{SessionInfo, VersionInfo};

use super::error::gateway_tool_error;

/// Structured payload returned by `openvas_test_connection`.
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct TestConnectionReport {
    gateway_url: String,
    gateway_status: String,
    api_version: String,
    gmp_version: String,
    session_user: String,
    session_state: String,
    session_expires_in: i64,
    read_only: bool,
    toolsets: String,
}

#[derive(Clone)]
pub struct GvmMcpServer {
    gateway: Arc<GatewayClient>,
    config: Arc<Config>,
}

#[tool_router]
impl GvmMcpServer {
    pub fn new(config: Config) -> anyhow::Result<Self> {
        let gateway = Arc::new(GatewayClient::new(&config)?);
        Ok(Self {
            gateway,
            config: Arc::new(config),
        })
    }

    /// Verify connectivity to the GVM stack: checks gateway liveness,
    /// queries the gvmd version and performs an authenticated session
    /// round-trip. Use this first if other tools fail.
    #[tool(
        name = "openvas_test_connection",
        annotations(title = "Test GVM connection", read_only_hint = true)
    )]
    pub async fn test_connection(&self) -> Result<CallToolResult, McpError> {
        let health = match self.gateway.health().await {
            Ok(health) => health,
            Err(err) => {
                return Ok(gateway_tool_error(
                    "checking gateway liveness (GET /health)",
                    &err,
                ));
            }
        };

        let version: VersionInfo = match self.gateway.version().await {
            Ok(version) => version,
            Err(err) => {
                return Ok(gateway_tool_error(
                    "querying gvmd version (GET /api/v1/version)",
                    &err,
                ));
            }
        };

        let session: SessionInfo = match self.gateway.session_info().await {
            Ok(session) => session,
            Err(err) => {
                return Ok(gateway_tool_error(
                    "authenticating a gateway session (POST/GET /api/v1/session)",
                    &err,
                ));
            }
        };

        let report = TestConnectionReport {
            gateway_url: self.config.gateway_url.to_string(),
            gateway_status: health.status,
            api_version: version.api_version,
            gmp_version: version.gmp_version,
            session_user: session.user,
            session_state: session.state,
            session_expires_in: session.expires_in,
            read_only: self.config.read_only,
            toolsets: self.config.toolsets.to_string(),
        };

        let text = serde_json::to_string_pretty(&report)
            .map_err(|err| McpError::internal_error(err.to_string(), None))?;
        Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
    }
}

#[tool_handler]
impl ServerHandler for GvmMcpServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
            .with_server_info(
                Implementation::new("gvm-mcp", env!("CARGO_PKG_VERSION"))
                    .with_title("OpenVAS / GVM MCP Server")
                    .with_website_url("https://github.com/clawosiris/openvas-mcp-server"),
            )
            .with_instructions(
                "Tools for driving Greenbone Vulnerability Management (OpenVAS): \
                 scan targets, tasks, reports and supporting resources. \
                 Start with openvas_test_connection to verify the stack is reachable.",
            )
    }
}
