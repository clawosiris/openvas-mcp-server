//! Port-lists toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "portCount", "tcpCount", "udpCount", "inUse"];

#[tool_router(router = port_lists_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List port lists targets can scan.
    #[tool(
        name = "openvas_list_port_lists",
        annotations(title = "List port lists", read_only_hint = true)
    )]
    pub async fn list_port_lists(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "port-lists",
            "portLists",
            ROW_KEYS,
            &params,
            "listing port lists",
        )
        .await
    }

    /// Get one port list by UUID, including its port ranges.
    #[tool(
        name = "openvas_get_port_list",
        annotations(title = "Get port list", read_only_hint = true)
    )]
    pub async fn get_port_list(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["port-lists", &params.id],
            "fetching the port list",
        )
        .await
    }
}
