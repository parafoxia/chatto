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

import asyncio
import hashlib
import json
import logging
import pathlib
import time
import typing as t

import aiofiles
from aiohttp.client import ClientSession

import chatto
from chatto import events
from chatto.errors import NoSecrets, NoSession
from chatto.secrets import Secrets
from chatto.ux import CLRS

log = logging.getLogger(__name__)

YOUTUBE_OAUTH_CHECK = "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token="


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


def get_token_refresh_data(
    token: str, *, secrets: Secrets
) -> tuple[dict[str, str], dict[str, str]]:
    data = {
        "client_id": secrets.client_id,
        "client_secret": secrets.client_secret,
        "grant_type": "refresh_token",
        "refresh_token": token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return data, headers


class OAuthMixin:
    events: events.EventHandler
    _session: ClientSession

    @property
    def session(self) -> ClientSession | None:
        ...

    @property
    def secrets(self) -> Secrets | None:
        return getattr(self, "_secrets", None)

    def use_secrets(self, path: pathlib.Path | str) -> None:
        self._secrets = Secrets.from_file(path)

    async def authorise(self, *, force: bool = False) -> None:
        log.info("Authorising bot")

        if not self.secrets:
            raise NoSecrets("you need to provide your secrets before authorising")

        if not self.session:
            raise NoSession("there is no active session")

        tokens_path = self._secrets.path.parent / "tokens.json"

        if force or not tokens_path.is_file():
            log.info("No tokens found -- authorisation required")
            self.tokens = await self._fetch_tokens(self._secrets, self._session)
            await self.set_tokens(self.tokens, tokens_path)
            return

        async with aiofiles.open(tokens_path) as f:
            tokens = json.loads(await f.read())

        async with self._session.get(YOUTUBE_OAUTH_CHECK + tokens["access_token"]) as r:
            token_expires_in = int((await r.json())["expires_in"])
            # Set this else this will more often than not be 3599.
            tokens["expires_in"] = token_expires_in

        if token_expires_in < 0:
            log.info("Token has expired -- refreshing")
            tokens = await self._refresh_tokens(self._secrets, self._session, tokens)
        else:
            log.info(f"Token expires in about {token_expires_in / 60:.0f} minutes")

        if not tokens:
            log.warning("Token refresh failed -- you will need to authorise manually")
            tokens = await self._fetch_tokens(self._secrets, self._session)

        await self.set_tokens(tokens, tokens_path)

    authorize = authorise

    async def set_tokens(self, tokens: dict[str, t.Any], path: pathlib.Path) -> None:
        self.tokens = tokens

        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(tokens))

        await self.events.dispatch(events.AuthorisedEvent, self.secrets, tokens)

    async def _fetch_tokens(
        self, secrets: Secrets, session: ClientSession
    ) -> dict[str, t.Any]:
        url, _ = get_auth_url(secrets)
        code = input(
            f"\33[1m{CLRS[4]}You need to authorise this session:\n{url}\n"
            "Paste code here: \33[0m"
        )
        data, headers = get_token_request_data(code, secrets=secrets)

        async with session.post(secrets.token_uri, data=data, headers=headers) as r:
            r.raise_for_status()
            return await r.json()  # type: ignore

    async def _refresh_tokens(
        self, secrets: Secrets, session: ClientSession, tokens: dict[str, t.Any]
    ) -> dict[str, t.Any]:
        data, headers = get_token_refresh_data(tokens["refresh_token"], secrets=secrets)

        async with session.post(secrets.token_uri, data=data, headers=headers) as r:
            if not r.ok:
                return {}

            data = await r.json()

        data.update({"refresh_token": tokens["refresh_token"]})
        return data

    async def auto_refresh_tokens(self, initial_delay: int) -> None:
        tokens_path = self._secrets.path.parent / "tokens.json"
        await asyncio.sleep(initial_delay)

        while True:
            await self.set_tokens(
                await self._refresh_tokens(self._secrets, self._session, self.tokens),
                tokens_path,
            )
            log.info("Token refreshed -- will repeat in one hour")
            await asyncio.sleep(3600)
