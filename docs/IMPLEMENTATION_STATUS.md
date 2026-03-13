# Implementation Status

This document replaces the old phase-by-phase planning docs.

## Completed

### Foundation
- [x] Project scaffold (`src/`, `tests/`, docs, workflows)
- [x] Poetry setup, Ruff, Mypy, Pytest
- [x] GVM client layer (base/local/remote)
- [x] Config loading (env + file)
- [x] Error hierarchy and validation utils
- [x] XML helper utilities

### Services Implemented
- [x] System service
- [x] Target service
- [x] Task (scan) service
- [x] Report service
- [x] Vulnerability service
- [x] Scan config service
- [x] Port list service
- [x] Schedule service
- [x] Note service
- [x] Override service
- [x] Ticket service
- [x] Asset service
- [x] Compliance service

### MCP Tooling
- [x] MCP server wiring for all implemented services
- [x] Toolsets registered under `src/presentation/mcp/toolsets/`
- [x] Structured JSON outputs from all tools

### CLI
- [x] Command groups for all implemented services
- [x] JSON-friendly outputs across commands
- [x] Rich table output on core command sets

### Testing
- [x] Unit tests for infrastructure and service layers
- [x] CI lint/type/test checks green

### Release / Delivery
- [x] Release workflow supports manual dispatch
- [x] CalVer tagging for manual release flow
- [x] CLI artifact upload in pipeline
- [x] Docker image build/push in release workflow

## Current Scope Summary
- Core implementation exists for all planned service domains.
- Remaining work is hardening depth (integration coverage, edge-case expansion, doc polish during deep review).

## Deep Review Checklist (for reviewer)
- [ ] Validate each service against real GMP responses
- [ ] Verify each MCP tool contract in live client
- [ ] Verify CLI UX and flag consistency
- [ ] Expand integration tests with real GVM environment
- [ ] Final docs pass (examples + troubleshooting)
