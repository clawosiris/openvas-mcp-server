//! Alerts toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &["id", "name", "event", "condition", "method", "inUse"];

#[tool_router(router = alerts_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List alerts (notifications triggered by task events).
    #[tool(
        name = "openvas_list_alerts",
        annotations(title = "List alerts", read_only_hint = true)
    )]
    pub async fn list_alerts(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "alerts",
            "alerts",
            ROW_KEYS,
            &params,
            "listing alerts",
        )
        .await
    }

    /// Get one alert by UUID, including event/condition/method data.
    #[tool(
        name = "openvas_get_alert",
        annotations(title = "Get alert", read_only_hint = true)
    )]
    pub async fn get_alert(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["alerts", &params.id],
            "fetching the alert",
        )
        .await
    }
}
