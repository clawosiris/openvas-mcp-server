from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.utils import attr, collect, text, validate_filter

from .models import HostAsset, OsAsset, TlsCertificateAsset

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class AssetService:
    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def list_hosts(self, filter_string: str = "") -> list[HostAsset]:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_assets(asset_type="host", filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        return collect(response, "asset", self._parse_host)

    def list_os(self, filter_string: str = "") -> list[OsAsset]:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_assets(asset_type="os", filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        return collect(response, "asset", self._parse_os)

    def list_tls_certificates(self, filter_string: str = "") -> list[TlsCertificateAsset]:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_assets(
                asset_type="tls-certificate",
                filter_string=filter_string or None,
            )

        response: Element = self._client.execute(operation)
        return collect(response, "asset", self._parse_tls)

    def _parse_host(self, elem: Element) -> HostAsset:
        return HostAsset(id=attr(elem, "id"), name=text(elem, "name"), ip=text(elem, "ip"))

    def _parse_os(self, elem: Element) -> OsAsset:
        return OsAsset(id=attr(elem, "id"), name=text(elem, "name"))

    def _parse_tls(self, elem: Element) -> TlsCertificateAsset:
        return TlsCertificateAsset(
            id=attr(elem, "id"),
            subject=text(elem, "subject"),
            issuer=text(elem, "issuer"),
        )
