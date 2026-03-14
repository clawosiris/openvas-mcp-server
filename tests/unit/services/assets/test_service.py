from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

from src.services.assets import AssetService


def test_list_asset_hosts() -> None:
    svc = AssetService(MagicMock())
    response = Element("get_assets_response", {"status": "200"})
    a = SubElement(response, "asset", {"id": "1"})
    SubElement(a, "name").text = "h"
    svc._client.execute.return_value = response
    out = svc.list_hosts()
    assert len(out) == 1
