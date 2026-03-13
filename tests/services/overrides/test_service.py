from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

from src.services.overrides import OverrideService


def test_list_overrides() -> None:
    svc = OverrideService(MagicMock())
    response = Element("get_overrides_response", {"status": "200"})
    o = SubElement(response, "override", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(o, "text").text = "x"
    svc._client.execute.return_value = response
    out = svc.list()
    assert out.total == 1
