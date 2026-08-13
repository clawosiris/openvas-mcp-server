//! Gateway HTTP client: request plumbing and per-request identity forwarding.
//!
//! The client holds no session. Every authorized request carries an
//! `Authorization` resolved per call by [`super::auth`]: the inbound caller's
//! header when present, otherwise a `Basic` header built from configured
//! gvmd credentials. The gateway (backed by gvmd) authorizes each request.

use reqwest::header::AUTHORIZATION;
use serde::de::DeserializeOwned;
use url::Url;

use crate::config::Config;

use super::auth::{basic_auth, current_authorization};
use super::error::{GatewayError, error_from_response};
use super::models::{HealthStatus, VersionInfo};

/// Path prefix of the versioned API surface. Liveness/readiness probes live
/// at the unversioned root.
const API_PREFIX: [&str; 2] = ["api", "v1"];

#[derive(Debug, Clone)]
pub struct GatewayClient {
    http: reqwest::Client,
    base_url: Url,
    /// `Authorization` used when the caller forwards none (stdio, or an HTTP
    /// caller that sent no credentials). Built once from configured gvmd
    /// credentials; `None` when none are configured.
    fallback_auth: Option<String>,
}

impl GatewayClient {
    pub fn new(config: &Config) -> anyhow::Result<Self> {
        let http = reqwest::Client::builder()
            .timeout(config.timeout)
            .user_agent(concat!("gvm-mcp/", env!("CARGO_PKG_VERSION")))
            .build()?;

        let fallback_auth = Self::fallback_auth(config);

        Ok(Self {
            http,
            base_url: config.gateway_url.clone(),
            fallback_auth,
        })
    }

    fn fallback_auth(config: &Config) -> Option<String> {
        match (&config.username, &config.password) {
            (Some(user), Some(pass)) => Some(basic_auth(user, pass)),
            _ => None,
        }
    }

    /// Test seam: build a client with an explicit fallback `Basic` credential.
    #[cfg(test)]
    pub fn with_basic_fallback(
        gateway_url: Url,
        username: &str,
        password: secrecy::SecretString,
    ) -> anyhow::Result<Self> {
        Ok(Self {
            http: reqwest::Client::builder().build()?,
            base_url: gateway_url,
            fallback_auth: Some(basic_auth(username, &password)),
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

    /// Authorized PUT under `/api/v1` with a JSON body, decoded as JSON.
    pub async fn put_json<T: DeserializeOwned>(
        &self,
        segments: &[&str],
        body: &impl serde::Serialize,
    ) -> Result<T, GatewayError> {
        let url = self.api_url(segments);
        let response = self
            .send_authorized(|http| http.put(url.clone()).json(body))
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

    /// Authorized GET under `/api/v1` returning raw bytes plus the
    /// `Content-Type` and `Content-Disposition` filename (artifact
    /// downloads, e.g. rendered report exports).
    pub async fn get_bytes(
        &self,
        segments: &[&str],
    ) -> Result<(Vec<u8>, Option<String>, Option<String>), GatewayError> {
        let url = self.api_url(segments);
        let response = self.send_authorized(|http| http.get(url.clone())).await?;
        if !response.status().is_success() {
            return Err(error_from_response(response).await);
        }

        let content_type = response
            .headers()
            .get(reqwest::header::CONTENT_TYPE)
            .and_then(|v| v.to_str().ok())
            .map(str::to_owned);
        let filename = response
            .headers()
            .get(reqwest::header::CONTENT_DISPOSITION)
            .and_then(|v| v.to_str().ok())
            .and_then(|v| v.split("filename=").nth(1))
            .map(|v| v.trim_matches('"').to_owned());
        let bytes = response.bytes().await?.to_vec();
        Ok((bytes, content_type, filename))
    }

    async fn get_unauthenticated<T: DeserializeOwned>(&self, url: Url) -> Result<T, GatewayError> {
        let response = self.http.get(url.clone()).send().await?;
        Self::decode(url, response).await
    }

    /// Send with the identity for the current request: the caller's forwarded
    /// `Authorization` if present, otherwise the configured fallback. If
    /// neither is available the request goes out unauthenticated and the
    /// gateway answers `401`. `build` constructs the request minus
    /// authorization.
    async fn send_authorized<F>(&self, build: F) -> Result<reqwest::Response, GatewayError>
    where
        F: Fn(&reqwest::Client) -> reqwest::RequestBuilder,
    {
        let mut request = build(&self.http);
        if let Some(authorization) = current_authorization(self.fallback_auth.as_deref()) {
            request = request.header(AUTHORIZATION, authorization);
        }
        Ok(request.send().await?)
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
