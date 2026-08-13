//! Schedules toolset: read surface plus create/update/delete.

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::CallToolResult;
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::Deserialize;

use crate::mcp::server::GvmMcpServer;

use super::common::{
    Body, DeleteParams, GetByIdParams, ListParams, create_resource, delete_resource,
    get_passthrough, list_summarized, update_resource,
};

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

    /// Create a scan schedule from an iCalendar definition. Not idempotent:
    /// repeating the call creates duplicates.
    #[tool(
        name = "openvas_create_schedule",
        annotations(
            title = "Create schedule",
            read_only_hint = false,
            destructive_hint = false
        )
    )]
    pub async fn create_schedule(
        &self,
        Parameters(params): Parameters<CreateScheduleParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set("name", params.name)
            .set("icalendar", params.icalendar)
            .set("timezone", params.timezone)
            .set_opt("comment", params.comment);
        create_resource(self.gateway(), "schedules", body, "creating the schedule").await
    }

    /// Update a scan schedule. Idempotent (PUT): omitted fields stay
    /// unchanged.
    #[tool(
        name = "openvas_update_schedule",
        annotations(
            title = "Update schedule",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn update_schedule(
        &self,
        Parameters(params): Parameters<UpdateScheduleParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = Body::new()
            .set_opt("name", params.name)
            .set_opt("comment", params.comment)
            .set_opt("icalendar", params.icalendar)
            .set_opt("timezone", params.timezone);
        update_resource(
            self.gateway(),
            &["schedules", &params.id],
            body,
            "updating the schedule",
        )
        .await
    }

    /// Delete a scan schedule (to the trashcan by default; `ultimate`
    /// deletes permanently). Fails with 409 if a task still uses it.
    #[tool(
        name = "openvas_delete_schedule",
        annotations(
            title = "Delete schedule",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn delete_schedule(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        delete_resource(
            self.gateway(),
            "schedules",
            &params,
            "deleting the schedule",
        )
        .await
    }
}

/// Arguments for `openvas_create_schedule`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct CreateScheduleParams {
    /// Schedule name
    pub name: String,
    /// iCalendar (RFC 5545) definition, e.g. a VEVENT with RRULE
    pub icalendar: String,
    /// IANA timezone, e.g. "UTC" or "Europe/Istanbul"
    pub timezone: String,
    /// Optional comment
    pub comment: Option<String>,
}

/// Arguments for `openvas_update_schedule`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct UpdateScheduleParams {
    /// UUID of the schedule to update
    pub id: String,
    pub name: Option<String>,
    pub comment: Option<String>,
    /// Replacement iCalendar (RFC 5545) definition
    pub icalendar: Option<String>,
    /// Replacement IANA timezone
    pub timezone: Option<String>,
}
