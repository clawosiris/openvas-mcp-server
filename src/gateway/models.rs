//! Serde DTOs mirroring the gateway's `openapi.yaml` (source of truth:
//! `rust-gvm-api` `spec/rest-api/`). Keep field names in lockstep with the
//! spec; the contract tests deserialize the documented examples.

use serde::{Deserialize, Serialize};

/// `POST /api/v1/session` — 201 response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionCreated {
    /// Opaque bearer token for subsequent requests.
    pub session_token: String,
    /// Idle timeout in seconds; the session expires if unused for this long.
    pub expires_in: u64,
    /// GMP protocol version.
    pub gmp_version: String,
}

/// `GET /api/v1/session` — 200 response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionInfo {
    pub user: String,
    /// `active` or `expired`.
    pub state: String,
    pub created_at: String,
    pub last_used_at: String,
    /// Remaining seconds until idle expiry.
    pub expires_in: i64,
}

/// `GET /health` — 200 response (unversioned root path).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    /// Liveness state (`ok`).
    pub status: String,
}

/// `GET /ready` — 200/503 response (unversioned root path).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadinessStatus {
    /// `ready` or `notReady`.
    pub status: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}

/// `GET /api/v1/version` — 200 response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct VersionInfo {
    /// REST API contract version, not the proxy binary version.
    pub api_version: String,
    /// GMP protocol version reported by the proxied gvmd.
    pub gmp_version: String,
}

/// Minimal reference to a related resource.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceRef {
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
}

/// `201 Created` envelope returned by all create endpoints.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceCreated {
    pub id: String,
}

/// A scan target as served by `GET /api/v1/targets[/{id}]`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Target {
    pub id: String,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub comment: Option<String>,
    pub hosts: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub exclude_hosts: Option<Vec<String>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub alive_test: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub port_list: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reverse_lookup_only: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reverse_lookup_unify: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ssh_credential: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub smb_credential: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub esxi_credential: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub snmp_credential: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub in_use: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub writable: Option<bool>,
}

/// `GET /api/v1/targets` — 200 response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TargetList {
    pub data: Vec<Target>,
    pub pagination: Pagination,
}

/// A scan task as served by `GET /api/v1/tasks[/{id}]`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Task {
    pub id: String,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub comment: Option<String>,
    /// Lifecycle status as reported by gvmd (`New`, `Running`, `Done`, …).
    /// Unknown future gvmd values are preserved.
    pub status: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub progress: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scan_config: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scanner: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schedule: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub alerts: Option<Vec<ResourceRef>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub alterable: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hosts_ordering: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schedule_periods: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_report: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub current_report: Option<ResourceRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub report_count: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub in_use: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub writable: Option<bool>,
}

/// `GET /api/v1/tasks` — 200 response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskList {
    pub data: Vec<Task>,
    pub pagination: Pagination,
}

/// `POST /api/v1/tasks` request body.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateTask {
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub comment: Option<String>,
    pub target_id: String,
    pub scan_config_id: String,
    pub scanner_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schedule_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub alert_ids: Option<Vec<String>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub alterable: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schedule_periods: Option<i32>,
}

/// `POST /api/v1/tasks/{id}/start|resume` — 200 response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TaskAction {
    /// UUID of the report created by the start/resume action.
    pub report_id: String,
}

/// Shared pagination envelope used by all gateway list endpoints.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Pagination {
    pub page: u32,
    pub per_page: u32,
    /// Total number of resources matching the query.
    pub total: u64,
    pub total_pages: u32,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn session_created_matches_spec_example() {
        let json = r#"{
            "sessionToken": "gvm_sess_9e6b2d4a8f1c",
            "expiresIn": 300,
            "gmpVersion": "22.7"
        }"#;
        let parsed: SessionCreated = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.session_token, "gvm_sess_9e6b2d4a8f1c");
        assert_eq!(parsed.expires_in, 300);
        assert_eq!(parsed.gmp_version, "22.7");
    }

    #[test]
    fn session_info_matches_spec_example() {
        let json = r#"{
            "user": "admin",
            "state": "active",
            "createdAt": "2026-08-09T21:00:00Z",
            "lastUsedAt": "2026-08-09T21:01:00Z",
            "expiresIn": 300
        }"#;
        let parsed: SessionInfo = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.user, "admin");
        assert_eq!(parsed.state, "active");
    }

    #[test]
    fn version_info_matches_spec_example() {
        let json = r#"{"apiVersion": "0.1.0", "gmpVersion": "22.7"}"#;
        let parsed: VersionInfo = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.api_version, "0.1.0");
        assert_eq!(parsed.gmp_version, "22.7");
    }

    #[test]
    fn target_matches_spec_shape() {
        let json = r#"{
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "webservers",
            "hosts": ["192.168.1.0/24"],
            "excludeHosts": ["192.168.1.1"],
            "aliveTest": "ICMP Ping",
            "portList": {"id": "pl-1", "name": "All TCP"},
            "inUse": false,
            "writable": true
        }"#;
        let parsed: Target = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.hosts, vec!["192.168.1.0/24"]);
        assert_eq!(parsed.port_list.unwrap().name.as_deref(), Some("All TCP"));
    }

    #[test]
    fn task_matches_spec_shape() {
        let json = r#"{
            "id": "t-1",
            "name": "weekly scan",
            "status": "Running",
            "progress": 42,
            "target": {"id": "tg-1", "name": "webservers"},
            "scanConfig": {"id": "sc-1", "name": "Full and fast"},
            "lastReport": {"id": "r-1"},
            "reportCount": 3
        }"#;
        let parsed: Task = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.status, "Running");
        assert_eq!(parsed.progress, Some(42));
        assert_eq!(parsed.report_count, Some(3));
    }

    #[test]
    fn create_task_serializes_camel_case_and_omits_none() {
        let body = CreateTask {
            name: "scan".into(),
            comment: None,
            target_id: "tg-1".into(),
            scan_config_id: "sc-1".into(),
            scanner_id: "s-1".into(),
            schedule_id: None,
            alert_ids: None,
            alterable: None,
            schedule_periods: None,
        };
        let json = serde_json::to_value(&body).unwrap();
        assert_eq!(json["targetId"], "tg-1");
        assert_eq!(json["scanConfigId"], "sc-1");
        assert!(json.get("comment").is_none());
        assert!(json.get("scheduleId").is_none());
    }

    #[test]
    fn pagination_matches_spec_example() {
        let json = r#"{"page": 1, "perPage": 25, "total": 142, "totalPages": 6}"#;
        let parsed: Pagination = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.per_page, 25);
        assert_eq!(parsed.total, 142);
    }
}
