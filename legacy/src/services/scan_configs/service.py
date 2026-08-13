# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Scan config service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import attr, collect, response_ok, text, to_int, validate_filter, validate_uuid

from .models import ScanConfig, ScanConfigListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class ScanConfigService:
    """Service for managing scan configurations."""

    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def get(self, config_id: str) -> ScanConfig:
        config_id = validate_uuid(config_id, "config_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_scan_config(config_id=config_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("scan_config", config_id)

        config_elem = response.find("config")
        if config_elem is None:
            raise ResourceNotFoundError("scan_config", config_id)

        return self._parse_scan_config(config_elem)

    def list(self, filter_string: str = "") -> ScanConfigListResponse:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_scan_configs(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        configs = collect(response, "config", self._parse_scan_config)

        return ScanConfigListResponse(
            scan_configs=configs,
            total=len(configs),
            filtered=len(configs),
        )

    def _parse_scan_config(self, elem: Element) -> ScanConfig:
        nvt_count = to_int(text(elem, "nvt_count"), 0)
        family_count = to_int(text(elem, "family_count"), 0)

        if nvt_count == 0:
            nvt_count = to_int(attr(elem, "nvt_count"), 0)
        if family_count == 0:
            family_count = to_int(attr(elem, "family_count"), 0)

        return ScanConfig(
            id=attr(elem, "id"),
            name=text(elem, "name"),
            family_count=family_count,
            nvt_count=nvt_count,
            comment=text(elem, "comment"),
        )
