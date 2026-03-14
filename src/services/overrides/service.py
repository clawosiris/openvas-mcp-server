# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import attr, collect, response_ok, text, validate_filter, validate_uuid

from .models import Override, OverrideListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class OverrideService:
    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def list(self, filter_string: str = "") -> OverrideListResponse:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_overrides(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        items = collect(response, "override", self._parse_override)
        return OverrideListResponse(overrides=items, total=len(items), filtered=len(items))

    def get(self, override_id: str) -> Override:
        override_id = validate_uuid(override_id, "override_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_override(override_id=override_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("override", override_id)
        elem = response.find("override")
        if elem is None:
            raise ResourceNotFoundError("override", override_id)
        return self._parse_override(elem)

    def create(self, text_value: str, nvt_oid: str = "") -> Override:
        def operation(gmp: Any) -> Any:
            return gmp.create_override(text=text_value, nvt_oid=nvt_oid or None)

        response: Element = self._client.execute(operation)
        return self.get(attr(response, "id") or text(response, "id"))

    def update(self, override_id: str, text_value: str) -> Override:
        override_id = validate_uuid(override_id, "override_id")

        def operation(gmp: Any) -> Any:
            return gmp.modify_override(override_id=override_id, text=text_value)

        self._client.execute(operation)
        return self.get(override_id)

    def delete(self, override_id: str) -> bool:
        override_id = validate_uuid(override_id, "override_id")

        def operation(gmp: Any) -> Any:
            return gmp.delete_override(override_id=override_id)

        response: Element = self._client.execute(operation)
        if attr(response, "status") == "404":
            raise ResourceNotFoundError("override", override_id)
        return response_ok(response)

    def _parse_override(self, elem: Element) -> Override:
        hosts = [h.text.strip() for h in elem.findall("hosts/host") if h.text]
        return Override(
            id=attr(elem, "id"),
            text=text(elem, "text"),
            nvt_oid=text(elem, "nvt/oid"),
            hosts=hosts,
            severity=text(elem, "severity"),
        )
