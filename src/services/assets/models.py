# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from pydantic import BaseModel


class HostAsset(BaseModel):
    id: str
    name: str = ""
    ip: str = ""


class OsAsset(BaseModel):
    id: str
    name: str = ""


class TlsCertificateAsset(BaseModel):
    id: str
    subject: str = ""
    issuer: str = ""
