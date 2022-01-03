# Copyright (c) 2021-2022, Ethan Henderson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from __future__ import annotations

import json
import logging
import os
import pathlib
import typing as t
from dataclasses import dataclass

import aiofiles

log = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    SecretT = str | list[str]


@dataclass(frozen=True)
class Secrets:
    client_id: str
    project_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_secret: str
    redirect_uris: list[str]
    path: pathlib.Path

    def __str__(self) -> str:
        return self.project_id

    def __getitem__(self, key: str) -> SecretT:
        return t.cast(SecretT, getattr(self, key))

    @classmethod
    def from_file(cls, path: pathlib.Path | str) -> Secrets:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        if not path.is_file():
            raise FileNotFoundError("you must provided a valid path to a secrets file")

        with open(path, encoding="utf-8") as f:
            log.info(f"Loading secrets from {path.resolve()}")
            data = json.load(f)["installed"]

        log.debug(f"Secrets data: {data}")
        return cls(**data, path=path)

    @classmethod
    async def afrom_file(cls, path: pathlib.Path | str) -> Secrets:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        if not os.path.isfile(path):
            raise FileNotFoundError("you must provided a valid path to a secrets file")

        async with aiofiles.open(path, encoding="utf-8") as f:
            log.info(f"Loading secrets from {path.resolve()}")
            data = json.loads(await f.read())["installed"]

        log.debug(f"Secrets data: {data}")
        return cls(**data)

    def to_dict(self) -> dict[str, SecretT]:
        return {
            "client_id": self.client_id,
            "project_id": self.project_id,
            "auth_uri": self.auth_uri,
            "token_uri": self.token_uri,
            "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
            "client_secret": self.client_secret,
            "redirect_uris": self.redirect_uris,
        }
