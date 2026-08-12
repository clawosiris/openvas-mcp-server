//! Shared tool parameter shapes and response helpers.

use rmcp::model::{CallToolResult, ContentBlock};
use rmcp::{ErrorData as McpError, schemars};
use serde::{Deserialize, Serialize};

/// Standard listing parameters shared by all gateway list endpoints.
#[derive(Debug, Default, Deserialize, schemars::JsonSchema)]
pub struct ListParams {
    /// GMP filter expression, e.g. `name~webserver and severity>5`
    pub filter: Option<String>,
    /// UUID of a saved filter to apply
    pub filter_id: Option<String>,
    /// Page number, 1-indexed (default 1)
    pub page: Option<u32>,
    /// Items per page, 1-1000 (default 25)
    pub per_page: Option<u32>,
}

impl ListParams {
    /// Map to the gateway's query parameters, omitting unset values.
    pub fn to_query(&self) -> Vec<(&'static str, String)> {
        let mut query = Vec::new();
        if let Some(filter) = &self.filter {
            query.push(("filter", filter.clone()));
        }
        if let Some(filter_id) = &self.filter_id {
            query.push(("filterId", filter_id.clone()));
        }
        if let Some(page) = self.page {
            query.push(("page", page.to_string()));
        }
        if let Some(per_page) = self.per_page {
            query.push(("perPage", per_page.to_string()));
        }
        query
    }
}

/// Parameters for tools that address one resource by UUID.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct GetByIdParams {
    /// Resource UUID
    pub id: String,
}

/// Parameters for delete tools.
#[derive(Debug, Deserialize, schemars::JsonSchema)]
pub struct DeleteParams {
    /// Resource UUID
    pub id: String,
    /// Permanently delete instead of moving to the trashcan (default false)
    pub ultimate: Option<bool>,
}

impl DeleteParams {
    pub fn to_query(&self) -> Vec<(&'static str, String)> {
        match self.ultimate {
            Some(ultimate) => vec![("ultimate", ultimate.to_string())],
            None => Vec::new(),
        }
    }
}

/// Render a serializable value as a successful JSON tool result.
pub fn json_result(value: &impl Serialize) -> Result<CallToolResult, McpError> {
    let text = serde_json::to_string_pretty(value)
        .map_err(|err| McpError::internal_error(err.to_string(), None))?;
    Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
}

/// Builder for gateway JSON request bodies. Tool arguments are snake_case
/// (Python-parity MCP surface); gateway bodies are camelCase — every `set*`
/// call names the gateway key explicitly, and unset optionals are omitted
/// entirely so the gateway's "absent means unchanged" semantics hold.
#[derive(Debug, Default)]
pub struct Body(serde_json::Map<String, serde_json::Value>);

impl Body {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn set(mut self, key: &str, value: impl Into<serde_json::Value>) -> Self {
        self.0.insert(key.to_string(), value.into());
        self
    }

    pub fn set_opt(self, key: &str, value: Option<impl Into<serde_json::Value>>) -> Self {
        match value {
            Some(value) => self.set(key, value),
            None => self,
        }
    }

    pub fn into_value(self) -> serde_json::Value {
        serde_json::Value::Object(self.0)
    }
}

/// Generic create tool body: POST and return the gateway's `{id}` envelope.
pub async fn create_resource(
    gateway: &crate::gateway::GatewayClient,
    resource: &str,
    body: Body,
    stage: &str,
) -> Result<CallToolResult, McpError> {
    match gateway
        .post_json::<serde_json::Value>(&[resource], &body.into_value())
        .await
    {
        Ok(created) => json_result(&created),
        Err(err) => Ok(crate::mcp::error::gateway_tool_error(stage, &err)),
    }
}

/// Generic update tool body: PUT and pass the updated resource through.
pub async fn update_resource(
    gateway: &crate::gateway::GatewayClient,
    segments: &[&str],
    body: Body,
    stage: &str,
) -> Result<CallToolResult, McpError> {
    match gateway
        .put_json::<serde_json::Value>(segments, &body.into_value())
        .await
    {
        Ok(updated) => json_result(&updated),
        Err(err) => Ok(crate::mcp::error::gateway_tool_error(stage, &err)),
    }
}

/// Generic delete tool body (204 expected; `ultimate` skips the trashcan).
pub async fn delete_resource(
    gateway: &crate::gateway::GatewayClient,
    resource: &str,
    params: &DeleteParams,
    stage: &str,
) -> Result<CallToolResult, McpError> {
    match gateway
        .delete(&[resource, &params.id], &params.to_query())
        .await
    {
        Ok(()) => json_result(&serde_json::json!({ "deleted": true, "id": params.id })),
        Err(err) => Ok(crate::mcp::error::gateway_tool_error(stage, &err)),
    }
}

/// Copy only `keys` (that are present and non-null) out of a JSON object.
/// Used to summarize gateway list rows: the key sets come from the gateway
/// spec, the summaries keep tool output within an LLM's token budget.
pub fn pick(value: &serde_json::Value, keys: &[&str]) -> serde_json::Value {
    let mut out = serde_json::Map::new();
    if let Some(object) = value.as_object() {
        for key in keys {
            if let Some(v) = object.get(*key)
                && !v.is_null()
            {
                out.insert((*key).to_string(), v.clone());
            }
        }
    }
    serde_json::Value::Object(out)
}

/// Generic list tool body: fetch `{data, pagination}` from the gateway,
/// summarize each row down to `keys`, and return `{<out_key>, pagination}`.
pub async fn list_summarized(
    gateway: &crate::gateway::GatewayClient,
    resource: &str,
    out_key: &str,
    keys: &[&str],
    params: &ListParams,
    stage: &str,
) -> Result<CallToolResult, McpError> {
    let value: serde_json::Value = match gateway
        .get_json_query(&[resource], &params.to_query())
        .await
    {
        Ok(value) => value,
        Err(err) => return Ok(crate::mcp::error::gateway_tool_error(stage, &err)),
    };

    let rows: Vec<serde_json::Value> = value["data"]
        .as_array()
        .map(|data| data.iter().map(|row| pick(row, keys)).collect())
        .unwrap_or_default();

    let mut out = serde_json::Map::new();
    out.insert(out_key.to_string(), serde_json::Value::Array(rows));
    if let Some(pagination) = value.get("pagination")
        && !pagination.is_null()
    {
        out.insert("pagination".to_string(), pagination.clone());
    }
    json_result(&serde_json::Value::Object(out))
}

/// Generic get tool body: fetch one resource and pass the gateway's JSON
/// through unchanged (the gateway spec is the contract; full detail is the
/// point of a get tool).
pub async fn get_passthrough(
    gateway: &crate::gateway::GatewayClient,
    segments: &[&str],
    stage: &str,
) -> Result<CallToolResult, McpError> {
    match gateway.get_json::<serde_json::Value>(segments).await {
        Ok(value) => json_result(&value),
        Err(err) => Ok(crate::mcp::error::gateway_tool_error(stage, &err)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn list_params_map_to_gateway_query_names() {
        let params = ListParams {
            filter: Some("severity>5".into()),
            filter_id: None,
            page: Some(2),
            per_page: Some(50),
        };
        assert_eq!(
            params.to_query(),
            vec![
                ("filter", "severity>5".to_string()),
                ("page", "2".to_string()),
                ("perPage", "50".to_string()),
            ]
        );
    }

    #[test]
    fn empty_list_params_produce_no_query() {
        assert!(ListParams::default().to_query().is_empty());
    }

    #[test]
    fn delete_params_only_send_ultimate_when_set() {
        let plain = DeleteParams {
            id: "x".into(),
            ultimate: None,
        };
        assert!(plain.to_query().is_empty());

        let ultimate = DeleteParams {
            id: "x".into(),
            ultimate: Some(true),
        };
        assert_eq!(ultimate.to_query(), vec![("ultimate", "true".to_string())]);
    }
}
