//! Mock-gateway tests for report drill-down pages and the async export-job
//! lifecycle (create → poll → download/cancel), including the base64
//! envelope and inline-size cap for binary artifacts.

mod support;

use gvm_mcp::mcp::GvmMcpServer;
use gvm_mcp::mcp::tools::common::{GetByIdParams, ListParams};
use gvm_mcp::mcp::tools::reports::{ExportReportParams, ReportPageParams};
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock};
use support::{config_for, mount_login_once, problem_response};
use wiremock::matchers::{body_json, method, path, query_param};
use wiremock::{Mock, MockServer, ResponseTemplate};

fn text_of(result: &CallToolResult) -> String {
    result
        .content
        .iter()
        .filter_map(|block| match block {
            ContentBlock::Text(text) => Some(text.text.clone()),
            _ => None,
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn json_of(result: &CallToolResult) -> serde_json::Value {
    serde_json::from_str(&text_of(result)).expect("tool output must be JSON")
}

async fn server_with_login() -> (MockServer, GvmMcpServer) {
    let server = MockServer::start().await;
    mount_login_once(&server, "token-a").await;
    let mcp = GvmMcpServer::new(config_for(&server)).unwrap();
    (server, mcp)
}

fn result_list_body() -> serde_json::Value {
    serde_json::json!({
        "data": [{
            "id": "r-1", "name": "OpenSSH < 8.0", "host": "10.0.0.5",
            "port": "22/tcp", "severity": 7.5, "threat": "High",
            "description": "long text dropped from rows"
        }],
        "pagination": {"page": 1, "perPage": 25, "total": 1, "totalPages": 1}
    })
}

#[tokio::test]
async fn report_drilldown_pages_hit_nested_paths_with_filters() {
    let (server, mcp) = server_with_login().await;
    for page in ["results", "vulnerabilities", "errors", "closed-cves"] {
        Mock::given(method("GET"))
            .and(path(format!("/api/v1/reports/rep-1/{page}")))
            .and(query_param("filter", "severity>7"))
            .respond_with(ResponseTemplate::new(200).set_body_json(result_list_body()))
            .expect(1)
            .mount(&server)
            .await;
    }

    let params = || ReportPageParams {
        id: "rep-1".into(),
        list: ListParams {
            filter: Some("severity>7".into()),
            filter_id: None,
            page: None,
            per_page: None,
        },
    };

    let results = mcp.get_report_results(Parameters(params())).await.unwrap();
    assert_eq!(json_of(&results)["results"][0]["host"], "10.0.0.5");
    assert!(json_of(&results)["results"][0].get("description").is_none());

    let vulns = mcp
        .get_report_vulnerabilities(Parameters(params()))
        .await
        .unwrap();
    assert_eq!(json_of(&vulns)["vulnerabilities"][0]["threat"], "High");

    let errors = mcp.get_report_errors(Parameters(params())).await.unwrap();
    assert_eq!(json_of(&errors)["errors"][0]["id"], "r-1");

    let cves = mcp
        .get_report_closed_cves(Parameters(params()))
        .await
        .unwrap();
    assert_eq!(json_of(&cves)["closedCves"][0]["id"], "r-1");
}

#[tokio::test]
async fn report_tls_certificates_summarize() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/reports/rep-1/tls-certificates"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "data": [{
                "id": "tls-1", "host": "10.0.0.5", "port": 443,
                "subject": "CN=web01", "issuer": "CN=corp-ca",
                "notBefore": "2026-01-01T00:00:00Z", "notAfter": "2027-01-01T00:00:00Z",
                "fingerprintSha256": "ab:cd"
            }],
            "pagination": {"page": 1, "perPage": 25, "total": 1, "totalPages": 1}
        })))
        .mount(&server)
        .await;

    let result = mcp
        .get_report_tls_certificates(Parameters(ReportPageParams {
            id: "rep-1".into(),
            list: ListParams::default(),
        }))
        .await
        .unwrap();
    let json = json_of(&result);
    assert_eq!(json["tlsCertificates"][0]["subject"], "CN=web01");
    assert!(json["tlsCertificates"][0].get("notBefore").is_none());
}

#[tokio::test]
async fn export_report_defaults_to_json_format() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("POST"))
        .and(path("/api/v1/reports/rep-1/exports"))
        .and(body_json(serde_json::json!({"format": "json"})))
        .respond_with(ResponseTemplate::new(202).set_body_json(serde_json::json!({
            "id": "job-1", "kind": "report_export", "status": "queued",
            "createdAt": "2026-08-13T10:00:00Z",
            "report": {"id": "rep-1"}, "format": "json"
        })))
        .expect(1)
        .mount(&server)
        .await;

    let result = mcp
        .export_report(Parameters(ExportReportParams {
            id: "rep-1".into(),
            report_format_id: None,
            filter: None,
            filter_id: None,
        }))
        .await
        .unwrap();
    let json = json_of(&result);
    assert_eq!(json["id"], "job-1");
    assert_eq!(json["status"], "queued");
}

#[tokio::test]
async fn export_report_with_gvmd_format_and_filter() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("POST"))
        .and(path("/api/v1/reports/rep-1/exports"))
        .and(body_json(serde_json::json!({
            "reportFormatId": "rf-pdf",
            "filter": "severity>7"
        })))
        .respond_with(ResponseTemplate::new(202).set_body_json(serde_json::json!({
            "id": "job-2", "kind": "report_export", "status": "queued",
            "createdAt": "2026-08-13T10:00:00Z",
            "report": {"id": "rep-1"}, "format": "gvmd_report_format"
        })))
        .expect(1)
        .mount(&server)
        .await;

    let result = mcp
        .export_report(Parameters(ExportReportParams {
            id: "rep-1".into(),
            report_format_id: Some("rf-pdf".into()),
            filter: Some("severity>7".into()),
            filter_id: None,
        }))
        .await
        .unwrap();
    assert_eq!(json_of(&result)["id"], "job-2");
}

#[tokio::test]
async fn job_poll_and_cancel() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/jobs/job-1"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "job-1", "kind": "report_export", "status": "succeeded",
            "createdAt": "2026-08-13T10:00:00Z",
            "resultLocation": "/api/v1/jobs/job-1/result",
            "result": {"contentType": "application/pdf", "filename": "report.pdf", "size": 12345}
        })))
        .mount(&server)
        .await;
    Mock::given(method("DELETE"))
        .and(path("/api/v1/jobs/job-2"))
        .respond_with(ResponseTemplate::new(202))
        .mount(&server)
        .await;

    let job = mcp
        .get_job(Parameters(GetByIdParams { id: "job-1".into() }))
        .await
        .unwrap();
    assert_eq!(json_of(&job)["status"], "succeeded");

    let cancelled = mcp
        .cancel_job(Parameters(GetByIdParams { id: "job-2".into() }))
        .await
        .unwrap();
    assert_eq!(json_of(&cancelled)["cancelled"], true);
}

#[tokio::test]
async fn download_json_result_is_returned_inline() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/jobs/job-1/result"))
        .respond_with(ResponseTemplate::new(200).set_body_raw(
            serde_json::json!({"report": {"id": "rep-1"}, "results": []}).to_string(),
            "application/json",
        ))
        .mount(&server)
        .await;

    let result = mcp
        .download_job_result(Parameters(GetByIdParams { id: "job-1".into() }))
        .await
        .unwrap();
    assert_eq!(json_of(&result)["report"]["id"], "rep-1");
}

#[tokio::test]
async fn download_binary_result_is_base64_enveloped() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/jobs/job-1/result"))
        .respond_with(
            ResponseTemplate::new(200)
                .set_body_raw(b"%PDF-1.7 fake".to_vec(), "application/pdf")
                .insert_header("Content-Disposition", "attachment; filename=\"report.pdf\""),
        )
        .mount(&server)
        .await;

    let result = mcp
        .download_job_result(Parameters(GetByIdParams { id: "job-1".into() }))
        .await
        .unwrap();
    let json = json_of(&result);
    assert_eq!(json["contentType"], "application/pdf");
    assert_eq!(json["filename"], "report.pdf");
    use base64::Engine;
    let decoded = base64::engine::general_purpose::STANDARD
        .decode(json["base64"].as_str().unwrap())
        .unwrap();
    assert_eq!(decoded, b"%PDF-1.7 fake");
}

#[tokio::test]
async fn oversized_binary_result_is_refused_legibly() {
    let (server, mcp) = server_with_login().await;
    let big = vec![0u8; 3 * 1024 * 1024 + 1];
    Mock::given(method("GET"))
        .and(path("/api/v1/jobs/job-1/result"))
        .respond_with(ResponseTemplate::new(200).set_body_raw(big, "application/pdf"))
        .mount(&server)
        .await;

    let result = mcp
        .download_job_result(Parameters(GetByIdParams { id: "job-1".into() }))
        .await
        .unwrap();
    assert_eq!(result.is_error, Some(true));
    assert!(text_of(&result).contains("narrower filter"));
}

#[tokio::test]
async fn pending_job_result_conflict_is_legible() {
    let (server, mcp) = server_with_login().await;
    Mock::given(method("GET"))
        .and(path("/api/v1/jobs/job-1/result"))
        .respond_with(problem_response(
            409,
            "job_not_complete",
            "Job Not Complete",
        ))
        .mount(&server)
        .await;

    let result = mcp
        .download_job_result(Parameters(GetByIdParams { id: "job-1".into() }))
        .await
        .unwrap();
    assert_eq!(result.is_error, Some(true));
    assert!(text_of(&result).contains("Job Not Complete"));
}
