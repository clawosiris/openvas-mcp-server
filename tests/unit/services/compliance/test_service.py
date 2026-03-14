# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

from src.services.compliance import ComplianceService


def test_list_policies() -> None:
    svc = ComplianceService(MagicMock())
    response = Element("get_configs_response", {"status": "200"})
    c = SubElement(response, "config", {"id": "1"})
    SubElement(c, "name").text = "p"
    svc._client.execute.return_value = response
    out = svc.list_policies()
    assert out.total == 1
