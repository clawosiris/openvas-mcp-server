//! Overrides toolset: read surface (writes land in roadmap phase 3).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &[
    "id",
    "text",
    "nvt",
    "hosts",
    "severity",
    "newSeverity",
    "active",
];

#[tool_router(router = overrides_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List severity overrides.
    #[tool(
        name = "openvas_list_overrides",
        annotations(title = "List overrides", read_only_hint = true)
    )]
    pub async fn list_overrides(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "overrides",
            "overrides",
            ROW_KEYS,
            &params,
            "listing overrides",
        )
        .await
    }

    /// Get one severity override by UUID.
    #[tool(
        name = "openvas_get_override",
        annotations(title = "Get override", read_only_hint = true)
    )]
    pub async fn get_override(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["overrides", &params.id],
            "fetching the override",
        )
        .await
    }
}
