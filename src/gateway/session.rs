//! Gateway session lifecycle: lazy login, single-flight renewal.
//!
//! The gateway issues ephemeral bearer tokens (`POST /api/v1/session`, Basic
//! auth) with a short idle timeout. One [`SessionManager`] owns the token for
//! the whole server; every tool call borrows it. A 401 on an authorized
//! request triggers exactly one re-login even under concurrency: renewal
//! holds an async mutex, and late arrivals that raced on the same stale
//! session reuse the token the winner obtained.

use std::sync::Arc;

use secrecy::{ExposeSecret, SecretString};
use tokio::sync::Mutex;
use url::Url;

use super::error::{GatewayError, error_from_response};
use super::models::SessionCreated;

/// An authenticated gateway session. Compared by identity (`Arc::ptr_eq`)
/// during renewal to detect "someone already renewed for me".
pub struct Session {
    token: SecretString,
    pub expires_in: u64,
    pub gmp_version: String,
}

impl Session {
    pub fn bearer_token(&self) -> &str {
        self.token.expose_secret()
    }
}

impl std::fmt::Debug for Session {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Session")
            .field("token", &"[REDACTED]")
            .field("expires_in", &self.expires_in)
            .field("gmp_version", &self.gmp_version)
            .finish()
    }
}

pub struct SessionManager {
    http: reqwest::Client,
    session_url: Url,
    username: String,
    password: SecretString,
    current: Mutex<Option<Arc<Session>>>,
}

impl SessionManager {
    pub fn new(
        http: reqwest::Client,
        session_url: Url,
        username: String,
        password: SecretString,
    ) -> Self {
        Self {
            http,
            session_url,
            username,
            password,
            current: Mutex::new(None),
        }
    }

    /// Current session, logging in lazily on first use. Concurrent callers
    /// during the initial login are serialized on the mutex, so exactly one
    /// login request is sent.
    pub async fn current(&self) -> Result<Arc<Session>, GatewayError> {
        let mut guard = self.current.lock().await;
        if let Some(session) = guard.as_ref() {
            return Ok(Arc::clone(session));
        }
        let session = self.login().await?;
        *guard = Some(Arc::clone(&session));
        Ok(session)
    }

    /// Replace `stale` with a fresh session (single-flight). If another task
    /// already renewed while we waited for the lock, its session is returned
    /// without a second login.
    pub async fn renew(&self, stale: &Arc<Session>) -> Result<Arc<Session>, GatewayError> {
        let mut guard = self.current.lock().await;
        if let Some(session) = guard.as_ref()
            && !Arc::ptr_eq(session, stale)
        {
            return Ok(Arc::clone(session));
        }
        // Drop the stale token before logging in so a failed login does not
        // leave a known-bad session behind for other callers.
        *guard = None;
        let session = self.login().await?;
        *guard = Some(Arc::clone(&session));
        Ok(session)
    }

    async fn login(&self) -> Result<Arc<Session>, GatewayError> {
        tracing::debug!(user = %self.username, url = %self.session_url, "creating gateway session");
        let response = self
            .http
            .post(self.session_url.clone())
            .basic_auth(&self.username, Some(self.password.expose_secret()))
            .send()
            .await?;

        if !response.status().is_success() {
            let err = error_from_response(response).await;
            tracing::warn!(error = %err, "gateway session creation failed");
            return Err(err);
        }

        let created: SessionCreated =
            response
                .json()
                .await
                .map_err(|source| GatewayError::Decode {
                    endpoint: self.session_url.to_string(),
                    source,
                })?;

        tracing::debug!(
            expires_in = created.expires_in,
            gmp_version = %created.gmp_version,
            "gateway session created"
        );
        Ok(Arc::new(Session {
            token: SecretString::from(created.session_token),
            expires_in: created.expires_in,
            gmp_version: created.gmp_version,
        }))
    }
}

impl std::fmt::Debug for SessionManager {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SessionManager")
            .field("session_url", &self.session_url.as_str())
            .field("username", &self.username)
            .field("password", &"[REDACTED]")
            .finish_non_exhaustive()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn session_debug_redacts_token() {
        let session = Session {
            token: SecretString::from("super-secret"),
            expires_in: 300,
            gmp_version: "22.7".into(),
        };
        let debug = format!("{session:?}");
        assert!(!debug.contains("super-secret"));
        assert!(debug.contains("[REDACTED]"));
    }

    #[test]
    fn manager_debug_redacts_password() {
        let manager = SessionManager::new(
            reqwest::Client::new(),
            Url::parse("http://gw/api/v1/session").unwrap(),
            "admin".into(),
            SecretString::from("hunter2"),
        );
        let debug = format!("{manager:?}");
        assert!(!debug.contains("hunter2"));
    }
}
