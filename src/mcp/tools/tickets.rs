//! Tickets toolset: read surface (ticket writes are upstream-blocked in the
//! gateway; they land once `rust-gvm` supports them).

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "status", "assignedTo", "task"];

#[tool_router(router = tickets_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List remediation tickets.
    #[tool(
        name = "openvas_list_tickets",
        annotations(title = "List tickets", read_only_hint = true)
    )]
    pub async fn list_tickets(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "tickets",
            "tickets",
            ROW_KEYS,
            &params,
            "listing tickets",
        )
        .await
    }

    /// Get one remediation ticket by UUID, including its notes and the
    /// originating result.
    #[tool(
        name = "openvas_get_ticket",
        annotations(title = "Get ticket", read_only_hint = true)
    )]
    pub async fn get_ticket(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["tickets", &params.id],
            "fetching the ticket",
        )
        .await
    }
}
