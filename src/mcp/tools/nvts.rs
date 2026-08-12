//! NVTs toolset: read surface over vulnerability tests and their families.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::Deserialize;

use crate::mcp::server::GvmMcpServer;

use super::common::{ListParams, get_passthrough, list_summarized};

const ROW_KEYS: &[&str] = &[
    "oid",
    "name",
    "family",
    "severity",
    "cvssBase",
    "solutionType",
];

/// Arguments for `openvas_get_nvt` (NVTs are addressed by OID, not UUID).
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct GetNvtParams {
    /// NVT OID, e.g. `1.3.6.1.4.1.25623.1.0.100315`
    pub oid: String,
}

#[tool_router(router = nvts_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// Search NVTs (vulnerability tests) by GMP filter expression, e.g.
    /// `name~apache and severity>7`.
    #[tool(
        name = "openvas_search_nvts",
        annotations(title = "Search NVTs", read_only_hint = true)
    )]
    pub async fn search_nvts(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "nvts",
            "nvts",
            ROW_KEYS,
            &params,
            "searching NVTs",
        )
        .await
    }

    /// Get one NVT by OID, including tags and solution details.
    #[tool(
        name = "openvas_get_nvt",
        annotations(title = "Get NVT", read_only_hint = true)
    )]
    pub async fn get_nvt(
        &self,
        Parameters(params): Parameters<GetNvtParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(self.gateway(), &["nvts", &params.oid], "fetching the NVT").await
    }

    /// List NVT families with their test counts. Collection-only: no filter
    /// expressions, just pagination.
    #[tool(
        name = "openvas_list_nvt_families",
        annotations(title = "List NVT families", read_only_hint = true)
    )]
    pub async fn list_nvt_families(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "nvt-families",
            "families",
            &["name", "maxNvtCount"],
            &params,
            "listing NVT families",
        )
        .await
    }
}
