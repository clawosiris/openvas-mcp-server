//! Tags toolset: read surface.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, tool, tool_router};

use crate::mcp::server::GvmMcpServer;

use super::common::{GetByIdParams, ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &[
    "id",
    "name",
    "value",
    "resourceType",
    "resourceCount",
    "active",
];

#[tool_router(router = tags_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List tags attached to GVM resources.
    #[tool(
        name = "openvas_list_tags",
        annotations(title = "List tags", read_only_hint = true)
    )]
    pub async fn list_tags(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "tags",
            "tags",
            ROW_KEYS,
            &params,
            "listing tags",
        )
        .await
    }

    /// Get one tag by UUID, including the resources it is attached to.
    #[tool(
        name = "openvas_get_tag",
        annotations(title = "Get tag", read_only_hint = true)
    )]
    pub async fn get_tag(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(self.gateway(), &["tags", &params.id], "fetching the tag").await
    }
}
