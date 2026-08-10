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
    fn pagination_matches_spec_example() {
        let json = r#"{"page": 1, "perPage": 25, "total": 142, "totalPages": 6}"#;
        let parsed: Pagination = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.per_page, 25);
        assert_eq!(parsed.total, 142);
    }
}
