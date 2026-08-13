# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Target service module."""

from .models import (
    AliveTest,
    PortList,
    Target,
    TargetCreateRequest,
    TargetListResponse,
    TargetUpdateRequest,
)
from .service import TargetService

__all__ = [
    "Target",
    "TargetCreateRequest",
    "TargetUpdateRequest",
    "TargetListResponse",
    "AliveTest",
    "PortList",
    "TargetService",
]
