//! Feeds toolset: feed status reads.

use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{ListParams, list_summarized};

#[tool_router(router = feeds_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// Get the status of all feeds (NVT, CERT, SCAP, GVMD_DATA), including
    /// versions and whether a sync is in progress.
    #[tool(
        name = "openvas_list_feeds",
        annotations(title = "List feed status", read_only_hint = true)
    )]
    pub async fn list_feeds(&self) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "feeds",
            "feeds",
            &["type", "name", "version", "currentlySyncing"],
            &ListParams::default(),
            "listing feeds",
        )
        .await
    }
}
