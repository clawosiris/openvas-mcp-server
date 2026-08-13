# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Current |

We support the latest minor release with security patches. Once a new minor or major version is published, prior versions receive patches only for critical vulnerabilities at maintainer discretion.

## Reporting a Vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

Instead, use **GitHub Private Vulnerability Reporting**:

1. Go to the [Security Advisories](https://github.com/greenbone-hive/openvas-mcp-server/security/advisories) tab
2. Click **"Report a vulnerability"**
3. Fill in the details — affected component(s), reproduction steps, and impact assessment

### What to expect

- **Acknowledgment** within 48 hours
- **Initial assessment** within 5 business days
- **Patch timeline** depends on severity:
  - **Critical / High**: Target fix within 7 days
  - **Medium**: Target fix within 30 days
  - **Low**: Next scheduled release
- We will coordinate disclosure timing with you. We follow [responsible disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure) practices.

### What qualifies

- Credential exposure in tool responses, logs, or headers (the server holds
  gvmd credentials and a gateway bearer token — neither must ever leak)
- Authentication/authorization bypass in the streamable-HTTP transport
  (e.g. Host-header/DNS-rebinding protection failures)
- Injection reaching the gateway or gvmd through unvalidated tool arguments
- Improper input validation leading to resource exhaustion (DoS)
- TLS/transport layer vulnerabilities in the gateway client
- Dependency vulnerabilities with a viable attack path through our code

### What doesn't qualify

- Issues in upstream dependencies without a demonstrated attack path through
  openvas-mcp-server
- Vulnerabilities in the rust-gvm-api gateway or gvmd themselves (report those
  to their respective projects)
- Rate limiting or brute-force concerns (expected to be handled by deployment
  infrastructure, e.g. a reverse proxy)

## Security Measures

### Dependency Auditing

- **[cargo-audit](https://github.com/rustsec/rustsec)** runs in CI on every push and weekly via the Security workflow
- **[cargo-machete](https://github.com/bnjbvr/cargo-machete)** checks for unused dependencies in CI
- **[Semgrep](https://semgrep.dev/)** static analysis (`p/rust`, `p/security-audit`, `p/secrets`) runs in the Security workflow
- **[Dependabot](https://docs.github.com/en/code-security/dependabot)** monitors Cargo, GitHub Actions and Docker dependencies with weekly update PRs

### Code Quality

- `cargo clippy` with `-D warnings` in CI
- `#![forbid(unsafe_code)]` — no unsafe blocks anywhere in the crate
- Credentials wrapped in `secrecy::SecretString`; redacted from `Debug` output and never returned in tool responses
- SBOM (CycloneDX) generated and attached to every release

### Authentication

- **Outbound**: the server authenticates to the rust-gvm-api gateway with a gvmd account, using an ephemeral bearer session (`POST /api/v1/session`) that is renewed automatically. Credentials are never logged or returned.
- **Inbound (streamable HTTP)**: unauthenticated by default. Set `MCP_AUTH_TOKEN` to require `Authorization: Bearer <token>` (constant-time compared), and/or front the endpoint with an authenticating, TLS-terminating reverse proxy. `MCP_ALLOWED_HOSTS` is a DNS-rebinding guard, not authentication. Do not expose an unauthenticated HTTP endpoint beyond a trusted network.
- **stdio** has no network surface; access is process-level.

## Changelog

| Date | Change |
|------|--------|
| 2026-08-13 | Initial security policy |
