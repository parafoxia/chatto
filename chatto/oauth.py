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

import hashlib
import json
import logging
import pathlib
import time

import aiofiles

import chatto
from chatto.errors import NoSecrets, NoSession
from chatto.secrets import Secrets
from chatto.ux import CLRS

log = logging.getLogger(__name__)


def create_state() -> str:
    return hashlib.sha256(f"{time.time()}".encode("utf-8")).hexdigest()


def get_auth_url(secrets: Secrets) -> tuple[str, str]:
    state = create_state()
    auth_url = secrets.auth_uri + (
        "?response_type=code"
        f"&client_id={secrets.client_id}"
        f"&redirect_uri={secrets.redirect_uris[0]}"
        f"&scope={'+'.join(chatto.YOUTUBE_API_SCOPES)}"
        f"&state={state}"
    )
    return auth_url, state


def get_token_request_data(
    code: str, *, secrets: Secrets
) -> tuple[dict[str, str], dict[str, str]]:
    data = {
        "client_id": secrets.client_id,
        "client_secret": secrets.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": secrets.redirect_uris[0],
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return data, headers


class OAuthMixin:
    @property
    def secrets(self) -> Secrets | None:
        return getattr(self, "_secrets", None)

    def use_secrets(self, path: pathlib.Path | str) -> None:
        self._secrets = Secrets.from_file(path)

    async def authorise(self, *, force: bool = False) -> None:
        secrets = self.secrets
        if not secrets:
            raise NoSecrets("you need to provide your secrets before authorising")

        session = self.session  # type: ignore
        if not session:
            raise NoSession("there is no active session")

        tokens_path = secrets.path.parent / "tokens.json"
        if not force and tokens_path.is_file():
            log.info("Loading tokens from file")
            async with aiofiles.open(tokens_path) as f:
                self.oauth_tokens = json.loads(await f.read())
            return

        url, _ = get_auth_url(secrets)
        code = input(
            f"\33[1m{CLRS[4]}You need to authorise this session:\n{url}\n"
            "Paste code here: \33[0m"
        )
        data, headers = get_token_request_data(code, secrets=secrets)
        log.debug(f"Request data: {data}")
        log.debug(f"Req. headers: {headers}")

        async with session.post(secrets.token_uri, data=data, headers=headers) as r:
            r.raise_for_status()
            self.oauth_tokens = await r.json()

        async with aiofiles.open(tokens_path, "w") as f:
            log.info(f"Storing tokens to {tokens_path.resolve()}")
            await f.write(json.dumps(self.oauth_tokens))

    authorize = authorise
