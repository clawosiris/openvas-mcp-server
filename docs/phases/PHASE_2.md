# Phase 2: Service Layer

**Duration:** 4-5 days  
**Status:** Planning

---

## Overview

Domain-based services using the client layer. Each service has:
- `models.py` — Pydantic models
- `service.py` — Implementation

---

## 2.1 Target Service

```python
class TargetService:
    def list(filter: str = "") -> TargetListResponse
    def get(id: str) -> Target
    def create(request: TargetCreateRequest) -> Target
    def delete(id: str, ultimate: bool = False) -> None
```

---

## 2.2 Scan Service

```python
class ScanService:
    def list(filter: str = "") -> ScanListResponse
    def get(id: str) -> Scan
    def create(request: ScanCreateRequest) -> Scan
    def start(id: str) -> None
    def stop(id: str) -> None
    def get_status(id: str) -> ScanStatus
    def delete(id: str) -> None
```

---

## 2.3 Report Service

```python
class ReportService:
    def list(filter: str = "") -> ReportListResponse
    def get(id: str) -> Report
    def get_summary(id: str) -> ReportSummary
    def export(id: str, format: str) -> bytes
    def delete(id: str) -> None
```

---

## 2.4 Vulnerability Service

```python
class VulnerabilityService:
    def list(report_id: str) -> VulnerabilityListResponse
    def get(id: str) -> Vulnerability
    def search_nvts(query: str) -> list[NVT]
```

---

## 2.5 Note Service

```python
class NoteService:
    def list(filter: str = "") -> NoteListResponse
    def get(id: str) -> Note
    def create(request: NoteCreateRequest) -> Note
    def update(id: str, request: NoteUpdateRequest) -> Note
    def delete(id: str) -> None
```

---

## 2.6 Override Service

```python
class OverrideService:
    def list(filter: str = "") -> OverrideListResponse
    def get(id: str) -> Override
    def create(request: OverrideCreateRequest) -> Override
    def update(id: str, request: OverrideUpdateRequest) -> Override
    def delete(id: str) -> None
```

---

## 2.7 Compliance Service

```python
class ComplianceService:
    def list_policies() -> PolicyListResponse
    def list_audits(filter: str = "") -> AuditListResponse
    def get_audit(id: str) -> Audit
    def start_audit(request: AuditStartRequest) -> Audit
    def stop_audit(id: str) -> None
    def get_compliance_status(target_id: str) -> ComplianceStatus
```

---

## 2.8 Ticket Service

```python
class TicketService:
    def list(filter: str = "") -> TicketListResponse
    def get(id: str) -> Ticket
    def create(request: TicketCreateRequest) -> Ticket
    def update(id: str, request: TicketUpdateRequest) -> Ticket
    def delete(id: str) -> None
```

---

## 2.9 Asset Service

```python
class AssetService:
    def list_hosts(filter: str = "") -> HostAssetListResponse
    def list_os(filter: str = "") -> OsAssetListResponse
    def list_tls_certificates(filter: str = "") -> TlsCertListResponse
```

---

## 2.10 System Service

```python
class SystemService:
    def get_version() -> VersionInfo
    def get_status() -> SystemStatus
    def list_scan_configs() -> ScanConfigListResponse
    def list_port_lists() -> PortListListResponse
    def list_credentials() -> CredentialListResponse
```

---

## Deliverables

- [ ] All service implementations
- [ ] Pydantic models for all entities
- [ ] Edge-case unit tests
