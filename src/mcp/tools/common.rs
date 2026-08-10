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
