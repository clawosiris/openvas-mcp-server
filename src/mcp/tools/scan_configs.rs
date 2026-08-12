//! Scan-configs toolset: read surface plus create/update/delete.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::Deserialize;

use crate::mcp::server::GvmMcpServer;

use super::common::{
    Body, DeleteParams, GetByIdParams, ListParams, create_resource, delete_resource,
    get_passthrough, list_summarized, update_resource,
};

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

    /// Create a scan configuration, optionally cloned from a base config.
    /// Not idempotent: repeating the call creates duplicates.
    #[tool(
        name = "openvas_create_scan_config",
        annotations(
            title = "Create scan config",
            read_only_hint = false,
            destructive_hint = false
        )
    )]
    pub async fn create_scan_config(
        &self,
        Parameters(params): Parameters<CreateScanConfigParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set("name", params.name)
            .set_opt("comment", params.comment)
            .set_opt("baseScanConfigId", params.base_scan_config_id);
        create_resource(
            self.gateway(),
            "scan-configs",
            body,
            "creating the scan config",
        )
        .await
    }

    /// Rename or re-comment a scan configuration. Idempotent (PUT); fails
    /// with 409 if the config is predefined or in use.
    #[tool(
        name = "openvas_update_scan_config",
        annotations(
            title = "Update scan config",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn update_scan_config(
        &self,
        Parameters(params): Parameters<UpdateScanConfigParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set_opt("name", params.name)
            .set_opt("comment", params.comment);
        update_resource(
            self.gateway(),
            &["scan-configs", &params.id],
            body,
            "updating the scan config",
        )
        .await
    }

    /// Delete a scan configuration (to the trashcan by default; `ultimate`
    /// deletes permanently). Fails with 409 if a task still uses it.
    #[tool(
        name = "openvas_delete_scan_config",
        annotations(
            title = "Delete scan config",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn delete_scan_config(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        delete_resource(
            self.gateway(),
            "scan-configs",
            &params,
            "deleting the scan config",
        )
        .await
    }
}

/// Arguments for `openvas_create_scan_config`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct CreateScanConfigParams {
    /// Scan config name
    pub name: String,
    /// Optional comment
    pub comment: Option<String>,
    /// UUID of an existing config to clone as the starting point
    pub base_scan_config_id: Option<String>,
}

/// Arguments for `openvas_update_scan_config`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct UpdateScanConfigParams {
    /// UUID of the scan config to update
    pub id: String,
    pub name: Option<String>,
    pub comment: Option<String>,
}
