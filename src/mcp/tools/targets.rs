//! Targets toolset: read surface plus create/update/delete.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::{Deserialize, Serialize};

use crate::gateway::models::{Pagination, Target, TargetList};
use crate::mcp::error::gateway_tool_error;
use crate::mcp::server::GvmMcpServer;

use super::common::{
    Body, DeleteParams, GetByIdParams, ListParams, create_resource, delete_resource, json_result,
    update_resource,
};

/// Summarized list row: compact on purpose (LLM token budget). Full details
/// come from `openvas_get_target`.
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct TargetRow {
    id: String,
    name: String,
    hosts: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    port_list: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    in_use: Option<bool>,
}

#[derive(Debug, Serialize)]
struct TargetListResult {
    targets: Vec<TargetRow>,
    pagination: Pagination,
}

fn summarize(target: Target) -> TargetRow {
    TargetRow {
        id: target.id,
        name: target.name,
        hosts: target.hosts,
        port_list: target.port_list.and_then(|pl| pl.name),
        in_use: target.in_use,
    }
}

#[tool_router(router = targets_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan targets. Returns summarized rows plus pagination; use
    /// openvas_get_target for full details of one target.
    #[tool(
        name = "openvas_list_targets",
        annotations(title = "List targets", read_only_hint = true)
    )]
    pub async fn list_targets(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        let list: TargetList = match self
            .gateway()
            .get_json_query(&["targets"], &params.to_query())
            .await
        {
            Ok(list) => list,
            Err(err) => return Ok(gateway_tool_error("listing targets", &err)),
        };

        json_result(&TargetListResult {
            targets: list.data.into_iter().map(summarize).collect(),
            pagination: list.pagination,
        })
    }

    /// Get one scan target by UUID, including credentials, alive test and
    /// port list bindings.
    #[tool(
        name = "openvas_get_target",
        annotations(title = "Get target", read_only_hint = true)
    )]
    pub async fn get_target(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self
            .gateway()
            .get_json::<Target>(&["targets", &params.id])
            .await
        {
            Ok(target) => json_result(&target),
            Err(err) => Ok(gateway_tool_error("fetching the target", &err)),
        }
    }

    /// Create a scan target from host entries. Not idempotent: repeating the
    /// call creates duplicates (the gateway rejects duplicate names with 400).
    #[tool(
        name = "openvas_create_target",
        annotations(
            title = "Create target",
            read_only_hint = false,
            destructive_hint = false
        )
    )]
    pub async fn create_target(
        &self,
        Parameters(params): Parameters<CreateTargetParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set("name", params.name)
            .set("hosts", params.hosts)
            .set_opt("comment", params.comment)
            .set_opt("excludeHosts", params.exclude_hosts)
            .set_opt("aliveTest", params.alive_test)
            .set_opt("portListId", params.port_list_id)
            .set_opt("reverseLookupOnly", params.reverse_lookup_only)
            .set_opt("reverseLookupUnify", params.reverse_lookup_unify)
            .set_opt("sshCredentialId", params.ssh_credential_id)
            .set_opt("smbCredentialId", params.smb_credential_id)
            .set_opt("esxiCredentialId", params.esxi_credential_id)
            .set_opt("snmpCredentialId", params.snmp_credential_id);
        create_resource(self.gateway(), "targets", body, "creating the target").await
    }

    /// Update a scan target. Idempotent (PUT): omitted fields stay unchanged;
    /// fails with 404 if the target does not exist, 409 if it is in use.
    #[tool(
        name = "openvas_update_target",
        annotations(
            title = "Update target",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn update_target(
        &self,
        Parameters(params): Parameters<UpdateTargetParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set_opt("name", params.name)
            .set_opt("comment", params.comment)
            .set_opt("hosts", params.hosts)
            .set_opt("excludeHosts", params.exclude_hosts)
            .set_opt("aliveTest", params.alive_test)
            .set_opt("portListId", params.port_list_id)
            .set_opt("reverseLookupOnly", params.reverse_lookup_only)
            .set_opt("reverseLookupUnify", params.reverse_lookup_unify)
            .set_opt("sshCredentialId", params.ssh_credential_id)
            .set_opt("smbCredentialId", params.smb_credential_id)
            .set_opt("esxiCredentialId", params.esxi_credential_id)
            .set_opt("snmpCredentialId", params.snmp_credential_id);
        update_resource(
            self.gateway(),
            &["targets", &params.id],
            body,
            "updating the target",
        )
        .await
    }

    /// Delete a scan target (to the trashcan by default; `ultimate` deletes
    /// permanently). Fails with 409 if a task still uses the target.
    #[tool(
        name = "openvas_delete_target",
        annotations(
            title = "Delete target",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn delete_target(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        delete_resource(self.gateway(), "targets", &params, "deleting the target").await
    }
}

/// Arguments for `openvas_create_target`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct CreateTargetParams {
    /// Target name
    pub name: String,
    /// Host entries: IPs, CIDR ranges, hostnames
    pub hosts: Vec<String>,
    /// Optional comment
    pub comment: Option<String>,
    /// Hosts to exclude from scans
    pub exclude_hosts: Option<Vec<String>>,
    /// Alive test method, e.g. "ICMP Ping" or "Consider Alive"
    pub alive_test: Option<String>,
    /// UUID of the port list to scan (gateway default applies when omitted)
    pub port_list_id: Option<String>,
    /// Only scan hosts that resolve via reverse lookup
    pub reverse_lookup_only: Option<bool>,
    /// Deduplicate hosts that reverse-resolve to the same name
    pub reverse_lookup_unify: Option<bool>,
    /// SSH credential UUID for authenticated scans
    pub ssh_credential_id: Option<String>,
    /// SMB credential UUID for authenticated scans
    pub smb_credential_id: Option<String>,
    /// ESXi credential UUID for authenticated scans
    pub esxi_credential_id: Option<String>,
    /// SNMP credential UUID for authenticated scans
    pub snmp_credential_id: Option<String>,
}

/// Arguments for `openvas_update_target`: all fields optional, omitted
/// fields stay unchanged.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct UpdateTargetParams {
    /// UUID of the target to update
    pub id: String,
    pub name: Option<String>,
    pub comment: Option<String>,
    /// Replacement host entries
    pub hosts: Option<Vec<String>>,
    pub exclude_hosts: Option<Vec<String>>,
    pub alive_test: Option<String>,
    pub port_list_id: Option<String>,
    pub reverse_lookup_only: Option<bool>,
    pub reverse_lookup_unify: Option<bool>,
    pub ssh_credential_id: Option<String>,
    pub smb_credential_id: Option<String>,
    pub esxi_credential_id: Option<String>,
    pub snmp_credential_id: Option<String>,
}
