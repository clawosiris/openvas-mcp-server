//! Assets toolset: host assets discovered by scans.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "ip", "hostname", "severity", "os"];

#[tool_router(router = assets_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List host assets discovered by scans, with highest severity and OS.
    #[tool(
        name = "openvas_list_asset_hosts",
        annotations(title = "List host assets", read_only_hint = true)
    )]
    pub async fn list_asset_hosts(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "hosts",
            "hosts",
            ROW_KEYS,
            &params,
            "listing host assets",
        )
        .await
    }

    /// Get one host asset by UUID.
    #[tool(
        name = "openvas_get_asset_host",
        annotations(title = "Get host asset", read_only_hint = true)
    )]
    pub async fn get_asset_host(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["hosts", &params.id],
            "fetching the host asset",
        )
        .await
    }
}
