# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

import pytest

from src.services.system import SystemService

pytestmark = pytest.mark.integration


def test_get_version(system_service: SystemService) -> None:
    version = system_service.get_version()

    assert version.gmp_version
    assert "22.5" in version.gmp_version
    assert version.backend_name == "gvmd"
