//! Credentials toolset: read surface (secrets never leave the gateway).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "type", "login", "inUse"];

#[tool_router(router = credentials_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List credentials usable for authenticated scans (metadata only, no
    /// secrets).
    #[tool(
        name = "openvas_list_credentials",
        annotations(title = "List credentials", read_only_hint = true)
    )]
    pub async fn list_credentials(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "credentials",
            "credentials",
            ROW_KEYS,
            &params,
            "listing credentials",
        )
        .await
    }

    /// Get one credential by UUID (metadata only, no secrets).
    #[tool(
        name = "openvas_get_credential",
        annotations(title = "Get credential", read_only_hint = true)
    )]
    pub async fn get_credential(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["credentials", &params.id],
            "fetching the credential",
        )
        .await
    }
}
