//! Scanners toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "host", "port", "type"];

#[tool_router(router = scanners_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scanner instances tasks can run on.
    #[tool(
        name = "openvas_list_scanners",
        annotations(title = "List scanners", read_only_hint = true)
    )]
    pub async fn list_scanners(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "scanners",
            "scanners",
            ROW_KEYS,
            &params,
            "listing scanners",
        )
        .await
    }

    /// Get one scanner by UUID.
    #[tool(
        name = "openvas_get_scanner",
        annotations(title = "Get scanner", read_only_hint = true)
    )]
    pub async fn get_scanner(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["scanners", &params.id],
            "fetching the scanner",
        )
        .await
    }
}
