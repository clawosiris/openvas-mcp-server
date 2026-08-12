//! Schedules toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "timezone", "firstRun", "nextRun", "inUse"];

#[tool_router(router = schedules_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan schedules with their next run times.
    #[tool(
        name = "openvas_list_schedules",
        annotations(title = "List schedules", read_only_hint = true)
    )]
    pub async fn list_schedules(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "schedules",
            "schedules",
            ROW_KEYS,
            &params,
            "listing schedules",
        )
        .await
    }

    /// Get one schedule by UUID, including its iCalendar definition.
    #[tool(
        name = "openvas_get_schedule",
        annotations(title = "Get schedule", read_only_hint = true)
    )]
    pub async fn get_schedule(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["schedules", &params.id],
            "fetching the schedule",
        )
        .await
    }
}
