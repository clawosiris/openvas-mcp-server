//! Gateway HTTP client: request plumbing, bearer injection, 401 retry.

use std::sync::Arc;

use reqwest::StatusCode;
use serde::de::DeserializeOwned;
use url::Url;

use crate::config::Config;

use super::error::{GatewayError, error_from_response};
use super::models::{HealthStatus, SessionInfo, VersionInfo};
use super::session::SessionManager;

/// Path prefix of the versioned API surface. Liveness/readiness probes live
/// at the unversioned root.
const API_PREFIX: [&str; 2] = ["api", "v1"];

#[derive(Debug, Clone)]
pub struct GatewayClient {
    http: reqwest::Client,
    base_url: Url,
    sessions: Arc<SessionManager>,
}

impl GatewayClient {
    pub fn new(config: &Config) -> anyhow::Result<Self> {
        let http = reqwest::Client::builder()
            .timeout(config.timeout)
            .user_agent(concat!("gvm-mcp/", env!("CARGO_PKG_VERSION")))
            .build()?;

        let session_url = join_url(&config.gateway_url, &["api", "v1", "session"]);
        let sessions = Arc::new(SessionManager::new(
            http.clone(),
            session_url,
            config.username.clone(),
            config.password.clone(),
        ));

        Ok(Self {
            http,
            base_url: config.gateway_url.clone(),
            sessions,
        })
    }

    /// URL under `/api/v1`.
    pub fn api_url(&self, segments: &[&str]) -> Url {
        let mut all = API_PREFIX.to_vec();
        all.extend_from_slice(segments);
        join_url(&self.base_url, &all)
    }

    /// URL at the unversioned root (health/readiness probes).
    pub fn root_url(&self, segments: &[&str]) -> Url {
        join_url(&self.base_url, segments)
    }

    /// `GET /health` — liveness, unauthenticated.
    pub async fn health(&self) -> Result<HealthStatus, GatewayError> {
        self.get_unauthenticated(self.root_url(&["health"])).await
    }

    /// `GET /api/v1/version` — gvmd version, unauthenticated.
    pub async fn version(&self) -> Result<VersionInfo, GatewayError> {
        self.get_unauthenticated(self.api_url(&["version"])).await
    }

    /// `GET /api/v1/session` — inspect the current session (authorized).
    pub async fn session_info(&self) -> Result<SessionInfo, GatewayError> {
        self.get_json(&["session"]).await
    }

    /// Authorized GET under `/api/v1`, decoded as JSON.
    pub async fn get_json<T: DeserializeOwned>(
        &self,
        segments: &[&str],
    ) -> Result<T, GatewayError> {
        self.get_json_query(segments, &[]).await
    }

    /// Authorized GET under `/api/v1` with query parameters, decoded as JSON.
    pub async fn get_json_query<T: DeserializeOwned>(
        &self,
        segments: &[&str],
        query: &[(&str, String)],
    ) -> Result<T, GatewayError> {
        let url = self.api_url(segments);
        let response = self
            .send_authorized(|http| http.get(url.clone()).query(query))
            .await?;
        Self::decode(url, response).await
    }

    /// Authorized POST under `/api/v1` with a JSON body, decoded as JSON.
    pub async fn post_json<T: DeserializeOwned>(
        &self,
        segments: &[&str],
        body: &impl serde::Serialize,
    ) -> Result<T, GatewayError> {
        let url = self.api_url(segments);
        let response = self
            .send_authorized(|http| http.post(url.clone()).json(body))
            .await?;
        Self::decode(url, response).await
    }

    /// Authorized bodyless POST under `/api/v1`, decoded as JSON.
    pub async fn post_action<T: DeserializeOwned>(
        &self,
        segments: &[&str],
    ) -> Result<T, GatewayError> {
        let url = self.api_url(segments);
        let response = self.send_authorized(|http| http.post(url.clone())).await?;
        Self::decode(url, response).await
    }

    /// Authorized bodyless POST under `/api/v1` where the response body (if
    /// any) carries no information (e.g. task stop).
    pub async fn post_action_empty(&self, segments: &[&str]) -> Result<(), GatewayError> {
        let url = self.api_url(segments);
        let response = self.send_authorized(|http| http.post(url.clone())).await?;
        Self::expect_success(response).await
    }

    /// Authorized DELETE under `/api/v1` (expects 204).
    pub async fn delete(
        &self,
        segments: &[&str],
        query: &[(&str, String)],
    ) -> Result<(), GatewayError> {
        let url = self.api_url(segments);
        let response = self
            .send_authorized(|http| http.delete(url.clone()).query(query))
            .await?;
        Self::expect_success(response).await
    }

    async fn get_unauthenticated<T: DeserializeOwned>(&self, url: Url) -> Result<T, GatewayError> {
        let response = self.http.get(url.clone()).send().await?;
        Self::decode(url, response).await
    }

    /// Send with the current session's bearer token; on 401, renew the
    /// session exactly once (single-flight across tasks) and retry once.
    /// `build` constructs the request minus authorization, so the retry can
    /// attach the renewed token.
    async fn send_authorized<F>(&self, build: F) -> Result<reqwest::Response, GatewayError>
    where
        F: Fn(&reqwest::Client) -> reqwest::RequestBuilder,
    {
        let session = self.sessions.current().await?;
        let response = build(&self.http)
            .bearer_auth(session.bearer_token())
            .send()
            .await?;
        if response.status() != StatusCode::UNAUTHORIZED {
            return Ok(response);
        }

        tracing::debug!(url = %response.url(), "session rejected (401), renewing and retrying once");
        let renewed = self.sessions.renew(&session).await?;
        Ok(build(&self.http)
            .bearer_auth(renewed.bearer_token())
            .send()
            .await?)
    }

    async fn expect_success(response: reqwest::Response) -> Result<(), GatewayError> {
        if response.status().is_success() {
            Ok(())
        } else {
            Err(error_from_response(response).await)
        }
    }

    async fn decode<T: DeserializeOwned>(
        url: Url,
        response: reqwest::Response,
    ) -> Result<T, GatewayError> {
        if !response.status().is_success() {
            return Err(error_from_response(response).await);
        }
        response
            .json()
            .await
            .map_err(|source| GatewayError::Decode {
                endpoint: url.to_string(),
                source,
            })
    }
}

/// Append path segments to a base URL, preserving any base path prefix
/// (e.g. a gateway mounted behind a reverse proxy at `/gvm`).
fn join_url(base: &Url, segments: &[&str]) -> Url {
    let mut url = base.clone();
    {
        let mut path = url
            .path_segments_mut()
            .expect("gateway URL validated as http(s) with a host");
        path.pop_if_empty();
        for segment in segments {
            path.push(segment);
        }
    }
    url
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn join_url_appends_segments() {
        let base = Url::parse("http://gw:8080").unwrap();
        assert_eq!(
            join_url(&base, &["api", "v1", "session"]).as_str(),
            "http://gw:8080/api/v1/session"
        );
    }

    #[test]
    fn join_url_preserves_base_path_prefix() {
        let base = Url::parse("http://proxy/gvm/").unwrap();
        assert_eq!(
            join_url(&base, &["health"]).as_str(),
            "http://proxy/gvm/health"
        );
    }
}
