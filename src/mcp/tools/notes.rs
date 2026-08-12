//! Notes toolset: read surface (writes land in roadmap phase 3).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "text", "nvt", "hosts", "port", "severity", "active"];

#[tool_router(router = notes_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List notes attached to scan results.
    #[tool(
        name = "openvas_list_notes",
        annotations(title = "List notes", read_only_hint = true)
    )]
    pub async fn list_notes(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "notes",
            "notes",
            ROW_KEYS,
            &params,
            "listing notes",
        )
        .await
    }

    /// Get one note by UUID.
    #[tool(
        name = "openvas_get_note",
        annotations(title = "Get note", read_only_hint = true)
    )]
    pub async fn get_note(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(self.gateway(), &["notes", &params.id], "fetching the note").await
    }
}
