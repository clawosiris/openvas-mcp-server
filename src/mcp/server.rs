//! rmcp server wiring: composes per-toolset routers according to the
//! toolset selection and read-only mode.

use std::sync::Arc;

use rmcp::handler::server::ServerHandler;
use rmcp::handler::server::router::tool::ToolRouter;
use rmcp::model::{Implementation, ServerCapabilities, ServerInfo};
use rmcp::tool_handler;

use crate::config::Config;
use crate::gateway::GatewayClient;
use crate::mcp::toolset::Toolset;

#[derive(Clone)]
pub struct GvmMcpServer {
    gateway: Arc<GatewayClient>,
    config: Arc<Config>,
    tool_router: ToolRouter<Self>,
}

impl GvmMcpServer {
    pub fn new(config: Config) -> anyhow::Result<Self> {
        let gateway = Arc::new(GatewayClient::new(&config)?);

        let mut tool_router = ToolRouter::new();
        for toolset in config.toolsets.iter() {
            match toolset {
                Toolset::System => tool_router += Self::system_router(),
                Toolset::Targets => tool_router += Self::targets_router(),
                Toolset::Tasks => tool_router += Self::tasks_router(),
                Toolset::ScanConfigs => tool_router += Self::scan_configs_router(),
                Toolset::Scanners => tool_router += Self::scanners_router(),
                Toolset::Schedules => tool_router += Self::schedules_router(),
                Toolset::Credentials => tool_router += Self::credentials_router(),
                Toolset::Alerts => tool_router += Self::alerts_router(),
                Toolset::PortLists => tool_router += Self::port_lists_router(),
                Toolset::Results => tool_router += Self::results_router(),
                Toolset::Reports => tool_router += Self::reports_router(),
                Toolset::Assets => tool_router += Self::assets_router(),
                Toolset::ReportFormats => tool_router += Self::report_formats_router(),
                Toolset::Filters => tool_router += Self::filters_router(),
                Toolset::Tags => tool_router += Self::tags_router(),
                Toolset::Notes => tool_router += Self::notes_router(),
                Toolset::Overrides => tool_router += Self::overrides_router(),
                Toolset::Nvts => tool_router += Self::nvts_router(),
                Toolset::Feeds => tool_router += Self::feeds_router(),
                Toolset::Tickets => tool_router += Self::tickets_router(),
                Toolset::Identity => tool_router += Self::identity_router(),
                // Vulnerabilities and standalone TLS certs have no gateway
                // endpoint yet; compliance waits on the gateway's audits API.
                Toolset::Vulnerabilities | Toolset::TlsCertificates | Toolset::Compliance => {}
            }
        }

        if config.read_only {
            tool_router.map.retain(|_, route| {
                route
                    .attr
                    .annotations
                    .as_ref()
                    .and_then(|annotations| annotations.read_only_hint)
                    .unwrap_or(false)
            });
        }

        Ok(Self {
            gateway,
            config: Arc::new(config),
            tool_router,
        })
    }

    pub(crate) fn gateway(&self) -> &GatewayClient {
        &self.gateway
    }

    pub(crate) fn config(&self) -> &Config {
        &self.config
    }

    /// Names of the tools this instance exposes, sorted. Used by tests and
    /// diagnostics; the MCP `list_tools` result is derived from the same
    /// router.
    pub fn tool_names(&self) -> Vec<String> {
        let mut names: Vec<String> = self
            .tool_router
            .map
            .keys()
            .map(|name| name.to_string())
            .collect();
        names.sort();
        names
    }
}

#[tool_handler(router = self.tool_router)]
impl ServerHandler for GvmMcpServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
            .with_server_info(
                Implementation::new("gvm-mcp", env!("CARGO_PKG_VERSION"))
                    .with_title("OpenVAS / GVM MCP Server")
                    .with_website_url("https://github.com/clawosiris/openvas-mcp-server"),
            )
            .with_instructions(
                "Tools for driving Greenbone Vulnerability Management (OpenVAS): \
                 scan targets, tasks, reports and supporting resources. \
                 Start with openvas_test_connection to verify the stack is reachable.",
            )
    }
}
