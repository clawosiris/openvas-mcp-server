# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

import pytest

from src.services.scan_configs import ScanConfigService

pytestmark = pytest.mark.integration


def test_list_scan_configs(scan_config_service: ScanConfigService) -> None:
    result = scan_config_service.list()

    assert result.total == len(result.scan_configs)
    assert result.filtered == len(result.scan_configs)
    for config in result.scan_configs:
        assert config.id
        assert config.name
