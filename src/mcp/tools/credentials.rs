//! Credentials toolset: reads (secrets never leave the gateway) plus
//! create/update/delete.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::Deserialize;

use crate::mcp::server::GvmMcpServer;

use super::common::{
    Body, DeleteParams, GetByIdParams, ListParams, create_resource, delete_resource,
    get_passthrough, list_summarized, update_resource,
};

const ROW_KEYS: &[&str] = &["id", "name", "type", "login", "inUse"];
const STORE_ROW_KEYS: &[&str] = &["id", "name", "provider", "default", "writable"];

#[tool_router(router = credentials_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List credentials usable for authenticated scans (metadata only, no
    /// secrets).
    #[tool(
        name = "openvas_list_credentials",
        annotations(title = "List credentials", read_only_hint = true)
    )]
    pub async fn list_credentials(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "credentials",
            "credentials",
            ROW_KEYS,
            &params,
            "listing credentials",
        )
        .await
    }

    /// List available credential stores (backends that credentials can be
    /// created in). Useful before creating a credential.
    #[tool(
        name = "openvas_list_credential_stores",
        annotations(title = "List credential stores", read_only_hint = true)
    )]
    pub async fn list_credential_stores(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "credential-stores",
            "credentialStores",
            STORE_ROW_KEYS,
            &params,
            "listing credential stores",
        )
        .await
    }

    /// Get one credential by UUID (metadata only, no secrets).
    #[tool(
        name = "openvas_get_credential",
        annotations(title = "Get credential", read_only_hint = true)
    )]
    pub async fn get_credential(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["credentials", &params.id],
            "fetching the credential",
        )
        .await
    }

    /// Create a credential for authenticated scans. `type` selects the
    /// credential kind: up (username+password), cc (client certificate),
    /// snmp, snmpv3 or pw. Not idempotent.
    #[tool(
        name = "openvas_create_credential",
        annotations(
            title = "Create credential",
            read_only_hint = false,
            destructive_hint = false
        )
    )]
    pub async fn create_credential(
        &self,
        Parameters(params): Parameters<CreateCredentialParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set("name", params.name)
            .set("type", params.credential_type)
            .set_opt("comment", params.comment)
            .set_opt("login", params.login)
            .set_opt("password", params.password)
            .set_opt("privateKey", params.private_key)
            .set_opt("certificate", params.certificate)
            .set_opt("community", params.community)
            .set_opt("authAlgorithm", params.auth_algorithm)
            .set_opt("privacyAlgorithm", params.privacy_algorithm)
            .set_opt("privacyPassword", params.privacy_password);
        create_resource(
            self.gateway(),
            "credentials",
            body,
            "creating the credential",
        )
        .await
    }

    /// Update a credential (the type cannot change). Idempotent (PUT):
    /// omitted fields stay unchanged.
    #[tool(
        name = "openvas_update_credential",
        annotations(
            title = "Update credential",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn update_credential(
        &self,
        Parameters(params): Parameters<UpdateCredentialParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set_opt("name", params.name)
            .set_opt("comment", params.comment)
            .set_opt("login", params.login)
            .set_opt("password", params.password)
            .set_opt("privateKey", params.private_key)
            .set_opt("certificate", params.certificate)
            .set_opt("community", params.community)
            .set_opt("authAlgorithm", params.auth_algorithm)
            .set_opt("privacyAlgorithm", params.privacy_algorithm)
            .set_opt("privacyPassword", params.privacy_password);
        update_resource(
            self.gateway(),
            &["credentials", &params.id],
            body,
            "updating the credential",
        )
        .await
    }

    /// Delete a credential (to the trashcan by default; `ultimate` deletes
    /// permanently). Fails with 409 if a target still uses it.
    #[tool(
        name = "openvas_delete_credential",
        annotations(
            title = "Delete credential",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn delete_credential(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        delete_resource(
            self.gateway(),
            "credentials",
            &params,
            "deleting the credential",
        )
        .await
    }
}

/// Arguments for `openvas_create_credential`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct CreateCredentialParams {
    /// Credential name
    pub name: String,
    /// Credential kind: up, cc, snmp, snmpv3 or pw
    #[serde(rename = "type")]
    pub credential_type: String,
    /// Optional comment
    pub comment: Option<String>,
    /// Login/username (up, snmp, snmpv3)
    pub login: Option<String>,
    /// Password (up, snmpv3)
    pub password: Option<String>,
    /// PEM private key (cc)
    pub private_key: Option<String>,
    /// PEM certificate (cc)
    pub certificate: Option<String>,
    /// SNMP community string (snmp)
    pub community: Option<String>,
    /// SNMPv3 auth algorithm (md5 or sha1)
    pub auth_algorithm: Option<String>,
    /// SNMPv3 privacy algorithm (aes or des)
    pub privacy_algorithm: Option<String>,
    /// SNMPv3 privacy password
    pub privacy_password: Option<String>,
}

/// Arguments for `openvas_update_credential`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct UpdateCredentialParams {
    /// UUID of the credential to update
    pub id: String,
    pub name: Option<String>,
    pub comment: Option<String>,
    pub login: Option<String>,
    pub password: Option<String>,
    pub private_key: Option<String>,
    pub certificate: Option<String>,
    pub community: Option<String>,
    pub auth_algorithm: Option<String>,
    pub privacy_algorithm: Option<String>,
    pub privacy_password: Option<String>,
}
