//! Scan-configs toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &[
    "id",
    "name",
    "comment",
    "familyCount",
    "nvtCount",
    "type",
    "inUse",
];

#[tool_router(router = scan_configs_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan configurations (e.g. "Full and fast"). Returns summarized
    /// rows plus pagination; use openvas_get_scan_config for full details.
    #[tool(
        name = "openvas_list_scan_configs",
        annotations(title = "List scan configs", read_only_hint = true)
    )]
    pub async fn list_scan_configs(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "scan-configs",
            "scanConfigs",
            ROW_KEYS,
            &params,
            "listing scan configs",
        )
        .await
    }

    /// Get one scan configuration by UUID.
    #[tool(
        name = "openvas_get_scan_config",
        annotations(title = "Get scan config", read_only_hint = true)
    )]
    pub async fn get_scan_config(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["scan-configs", &params.id],
            "fetching the scan config",
        )
        .await
    }
}
