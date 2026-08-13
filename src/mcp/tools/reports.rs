//! Reports toolset: reads, drill-down pages and asynchronous export jobs.

use base64::Engine;
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock};
use rmcp::{ErrorData as McpError, schemars, tool, tool_router};
use serde::Deserialize;

use crate::mcp::error::gateway_tool_error;
use crate::mcp::server::GvmMcpServer;

use super::common::{
    Body, DeleteParams, GetByIdParams, ListParams, delete_resource, get_passthrough, json_result,
    list_summarized, list_summarized_at,
};

const ROW_KEYS: &[&str] = &[
    "id",
    "task",
    "scanStart",
    "scanEnd",
    "severity",
    "resultCount",
];

/// Drill-down pages reuse the results row shape.
const RESULT_ROW_KEYS: &[&str] = &[
    "id",
    "name",
    "host",
    "port",
    "severity",
    "threat",
    "occurrences",
];

const TLS_ROW_KEYS: &[&str] = &[
    "id",
    "host",
    "port",
    "subject",
    "issuer",
    "notAfter",
    "fingerprintSha256",
];

/// Inline artifacts above this size are refused; ask for a JSON export or a
/// narrower filter instead. Keeps tool output within an LLM-usable budget.
const MAX_INLINE_ARTIFACT_BYTES: usize = 3 * 1024 * 1024;

/// Arguments for report drill-down pages: report UUID plus list filtering.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct ReportPageParams {
    /// Report UUID
    pub id: String,
    #[serde(flatten)]
    pub list: ListParams,
}

/// Arguments for `openvas_export_report`.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct ExportReportParams {
    /// Report UUID
    pub id: String,
    /// UUID of a gvmd report format (see openvas_list_report_formats).
    /// Omit to request the gateway's native JSON export.
    pub report_format_id: Option<String>,
    /// Optional GMP filter expression applied during generation
    pub filter: Option<String>,
    /// Optional saved filter UUID applied during generation
    pub filter_id: Option<String>,
}

#[tool_router(router = reports_router, vis = "pub(crate)")]
impl GvmMcpServer {
    /// List scan reports with severity and result counts.
    #[tool(
        name = "openvas_list_reports",
        annotations(title = "List reports", read_only_hint = true)
    )]
    pub async fn list_reports(
        &self,
        Parameters(params): Parameters<ListParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized(
            self.gateway(),
            "reports",
            "reports",
            ROW_KEYS,
            &params,
            "listing reports",
        )
        .await
    }

    /// Get one scan report by UUID (summary level: task, timing, severity,
    /// result counts).
    #[tool(
        name = "openvas_get_report",
        annotations(title = "Get report", read_only_hint = true)
    )]
    pub async fn get_report(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(
            self.gateway(),
            &["reports", &params.id],
            "fetching the report",
        )
        .await
    }

    /// Delete a scan report (to the trashcan by default; `ultimate` deletes
    /// permanently). The task itself is not affected.
    #[tool(
        name = "openvas_delete_report",
        annotations(
            title = "Delete report",
            read_only_hint = false,
            destructive_hint = true
        )
    )]
    pub async fn delete_report(
        &self,
        Parameters(params): Parameters<DeleteParams>,
    ) -> Result<CallToolResult, McpError> {
        delete_resource(self.gateway(), "reports", &params, "deleting the report").await
    }

    /// List the individual results (findings) inside one report. Supports
    /// GMP filter expressions like `severity>7`.
    #[tool(
        name = "openvas_get_report_results",
        annotations(title = "Report results", read_only_hint = true)
    )]
    pub async fn get_report_results(
        &self,
        Parameters(params): Parameters<ReportPageParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized_at(
            self.gateway(),
            &["reports", &params.id, "results"],
            "results",
            RESULT_ROW_KEYS,
            &params.list,
            "listing report results",
        )
        .await
    }

    /// List the vulnerabilities page of one report (aggregated findings).
    #[tool(
        name = "openvas_get_report_vulnerabilities",
        annotations(title = "Report vulnerabilities", read_only_hint = true)
    )]
    pub async fn get_report_vulnerabilities(
        &self,
        Parameters(params): Parameters<ReportPageParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized_at(
            self.gateway(),
            &["reports", &params.id, "vulnerabilities"],
            "vulnerabilities",
            RESULT_ROW_KEYS,
            &params.list,
            "listing report vulnerabilities",
        )
        .await
    }

    /// List scan errors recorded in one report (NVTs that failed to run).
    #[tool(
        name = "openvas_get_report_errors",
        annotations(title = "Report errors", read_only_hint = true)
    )]
    pub async fn get_report_errors(
        &self,
        Parameters(params): Parameters<ReportPageParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized_at(
            self.gateway(),
            &["reports", &params.id, "errors"],
            "errors",
            RESULT_ROW_KEYS,
            &params.list,
            "listing report errors",
        )
        .await
    }

    /// List CVEs that are closed (no longer detected) according to one
    /// report.
    #[tool(
        name = "openvas_get_report_closed_cves",
        annotations(title = "Report closed CVEs", read_only_hint = true)
    )]
    pub async fn get_report_closed_cves(
        &self,
        Parameters(params): Parameters<ReportPageParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized_at(
            self.gateway(),
            &["reports", &params.id, "closed-cves"],
            "closedCves",
            RESULT_ROW_KEYS,
            &params.list,
            "listing report closed CVEs",
        )
        .await
    }

    /// List TLS certificates discovered during the scan behind one report.
    #[tool(
        name = "openvas_get_report_tls_certificates",
        annotations(title = "Report TLS certificates", read_only_hint = true)
    )]
    pub async fn get_report_tls_certificates(
        &self,
        Parameters(params): Parameters<ReportPageParams>,
    ) -> Result<CallToolResult, McpError> {
        list_summarized_at(
            self.gateway(),
            &["reports", &params.id, "tls-certificates"],
            "tlsCertificates",
            TLS_ROW_KEYS,
            &params.list,
            "listing report TLS certificates",
        )
        .await
    }

    /// Start an asynchronous report export. Returns a job (usually
    /// `queued`); poll it with openvas_get_job, then fetch the artifact with
    /// openvas_download_job_result once the status is `succeeded`. Jobs and
    /// artifacts expire ~15 minutes after completion.
    #[tool(
        name = "openvas_export_report",
        annotations(title = "Export report", read_only_hint = true)
    )]
    pub async fn export_report(
        &self,
        Parameters(params): Parameters<ExportReportParams>,
    ) -> Result<CallToolResult, McpError> {
        let body = match &params.report_format_id {
            Some(format_id) => Body::new().set("reportFormatId", format_id.clone()),
            None => Body::new().set("format", "json"),
        }
        .set_opt("filter", params.filter)
        .set_opt("filterId", params.filter_id);

        match self
            .gateway()
            .post_json::<serde_json::Value>(&["reports", &params.id, "exports"], &body.into_value())
            .await
        {
            Ok(job) => json_result(&job),
            Err(err) => Ok(gateway_tool_error("starting the report export", &err)),
        }
    }

    /// Get the status of an asynchronous job (queued, running, succeeded,
    /// failed, cancelling, cancelled or expired).
    #[tool(
        name = "openvas_get_job",
        annotations(title = "Get job status", read_only_hint = true)
    )]
    pub async fn get_job(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        get_passthrough(self.gateway(), &["jobs", &params.id], "fetching the job").await
    }

    /// Cancel an asynchronous job you created.
    #[tool(
        name = "openvas_cancel_job",
        annotations(title = "Cancel job", read_only_hint = false, destructive_hint = true)
    )]
    pub async fn cancel_job(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        match self.gateway().delete(&["jobs", &params.id], &[]).await {
            Ok(()) => json_result(&serde_json::json!({ "cancelled": true, "id": params.id })),
            Err(err) => Ok(gateway_tool_error("cancelling the job", &err)),
        }
    }

    /// Download the artifact of a succeeded export job. JSON exports are
    /// returned inline; binary formats (PDF, XML, CSV…) are returned as
    /// base64 up to 3 MB — for larger artifacts, export with a narrower
    /// filter or use the JSON format.
    #[tool(
        name = "openvas_download_job_result",
        annotations(title = "Download job result", read_only_hint = true)
    )]
    pub async fn download_job_result(
        &self,
        Parameters(params): Parameters<GetByIdParams>,
    ) -> Result<CallToolResult, McpError> {
        let (bytes, content_type, filename) = match self
            .gateway()
            .get_bytes(&["jobs", &params.id, "result"])
            .await
        {
            Ok(artifact) => artifact,
            Err(err) => return Ok(gateway_tool_error("downloading the job result", &err)),
        };

        let is_json = content_type
            .as_deref()
            .is_some_and(|ct| ct.starts_with("application/json"));
        if is_json {
            let text = String::from_utf8_lossy(&bytes).into_owned();
            return Ok(CallToolResult::success(vec![ContentBlock::text(text)]));
        }

        if bytes.len() > MAX_INLINE_ARTIFACT_BYTES {
            return Ok(CallToolResult::error(vec![ContentBlock::text(format!(
                "Artifact is {} bytes ({}), larger than the {} byte inline limit. \
                 Export with a narrower filter, or use the JSON format and page \
                 through the results instead.",
                bytes.len(),
                content_type.as_deref().unwrap_or("unknown content type"),
                MAX_INLINE_ARTIFACT_BYTES
            ))]));
        }

        json_result(&serde_json::json!({
            "contentType": content_type,
            "filename": filename,
            "size": bytes.len(),
            "base64": base64::engine::general_purpose::STANDARD.encode(&bytes),
        }))
    }
}
