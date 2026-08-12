//! System toolset: connectivity and version tools.

use rmcp::model::{CallToolResult, ContentBlock};
use rmcp::{ErrorData as McpError, tool, tool_router};
use serde::Serialize;

use crate::gateway::models::{SessionInfo, VersionInfo};
use crate::mcp::error::gateway_tool_error;
use crate::mcp::server::GvmMcpServer;

use super::common::json_result;

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

#[tool_router(router = system_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// Verify connectivity to the GVM stack: checks gateway liveness,
    /// queries the gvmd version and performs an authenticated session
    /// round-trip. Use this first if other tools fail.
    #[tool(
        name = "openvas_test_connection",
        annotations(title = "Test GVM connection", read_only_hint = true)
    )]
    pub async fn test_connection(&self) -> Result<CallToolResult, McpError> {
        let health = match self.gateway().health().await {
            Ok(health) => health,
            Err(err) => {
                return Ok(gateway_tool_error(
                    "checking gateway liveness (GET /health)",
                    &err,
                ));
            }
        };

        let version: VersionInfo = match self.gateway().version().await {
            Ok(version) => version,
            Err(err) => {
                return Ok(gateway_tool_error(
                    "querying gvmd version (GET /api/v1/version)",
                    &err,
                ));
            }
        };

        let session: SessionInfo = match self.gateway().session_info().await {
            Ok(session) => session,
            Err(err) => {
                return Ok(gateway_tool_error(
                    "authenticating a gateway session (POST/GET /api/v1/session)",
                    &err,
                ));
            }
        };

        let report = TestConnectionReport {
            gateway_url: self.config().gateway_url.to_string(),
            gateway_status: health.status,
            api_version: version.api_version,
            gmp_version: version.gmp_version,
            session_user: session.user,
            session_state: session.state,
            session_expires_in: session.expires_in,
            read_only: self.config().read_only,
            toolsets: self.config().toolsets.to_string(),
        };

        let text = serde_json::to_string_pretty(&report)
            .map_err(|err| McpError::internal_error(err.to_string(), None))?;
        Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
    }

    /// Get the GVM REST API contract version and the GMP protocol version
    /// reported by gvmd.
    #[tool(
        name = "openvas_get_version",
        annotations(title = "Get GVM versions", read_only_hint = true)
    )]
    pub async fn get_version(&self) -> Result<CallToolResult, McpError> {
        match self.gateway().version().await {
            Ok(version) => json_result(&version),
            Err(err) => Ok(gateway_tool_error(
                "querying gvmd version (GET /api/v1/version)",
                &err,
            )),
        }
    }
}
