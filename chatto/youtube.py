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
import json
import logging
import traceback
import typing as t

from aiohttp import ClientSession

import chatto
from chatto import events, stream
from chatto.errors import HTTPError, MissingRequiredInformation, NoSession
from chatto.message import Message
from chatto.oauth import OAuthMixin

if t.TYPE_CHECKING:
    from asyncio.events import AbstractEventLoop

log = logging.getLogger(__name__)


class YouTubeBot(OAuthMixin):
    __slots__ = (
        "token",
        "channel_id",
        "_stream",
        "_loop",
        "_session",
        "_secrets",
        "commands",
        "events",
        "oauth_tokens",
    )

    def __init__(
        self,
        token: str,
        channel_id: str,
        log_level: int = logging.INFO,
        log_file: str | None = None,
    ) -> None:
        chatto.ux.setup_logging(log_level, log_file)
        chatto.ux.print_banner(
            f"Running version \33[1m{chatto.__version__}\33[0m. "
            "Use `\33[1mpython -m chatto\33[0m` for more info.\n"
        )

        self.token = token
        if not channel_id:
            raise MissingRequiredInformation("a channel ID must be provided")
        self.channel_id = channel_id
        self.events = events.EventHandler()
        self.oauth_tokens = {}

    @property
    def loop(self) -> AbstractEventLoop | None:
        return getattr(self, "_loop", None)

    @property
    def session(self) -> ClientSession | None:
        return getattr(self, "_session", None)

    @property
    def stream(self) -> stream.Stream | None:
        return getattr(self, "_stream", None)

    @property
    def authorised(self) -> bool:
        return bool(self.oauth_tokens)

    @property
    def access_token(self) -> str | None:
        return t.cast(str | None, self.oauth_tokens.get("access_token", None))

    @property
    def platform(self) -> str:
        return "youtube"

    async def create_session(self, loop: AbstractEventLoop) -> None:
        self._session = ClientSession(loop=loop)
        log.info("New session created")

    async def fetch_stream_info(self, stream_id: str | None = None) -> None:
        if not self.session:
            raise NoSession("no active session")

        if stream_id:
            self._stream = await stream.Stream.from_id(
                stream_id, self.token, self.session
            )
        else:
            self._stream = await stream.Stream.from_channel_id(
                self.channel_id, self.token, self.session
            )

        await self.events.dispatch(events.StreamFetchedEvent, self._stream)

    async def make_request(self, url: str) -> dict[str, t.Any]:
        log.debug(f"Making request to {url}")
        async with self._session.get(url) as r:
            log.debug(f"Request: {r}")
            data = await r.json()

        err = data.get("error", None)
        if err:
            raise HTTPError(err["code"], err["errors"][0]["message"])

        return t.cast(dict[str, t.Any], data)

    async def poll_for_messages(self) -> None:
        page_token = ""  # nosec: B105 false positive
        url = chatto.YOUTUBE_API_BASE_URL + (
            "/liveChat/messages"
            f"?key={self.token}"
            f"&liveChatId={self._stream.chat_id}"
            "&part=snippet,authorDetails"
        )

        while True:
            try:
                log.debug("Polling for new messages...")
                data = await self.make_request(url + f"&pageToken={page_token}")
                new_items = data["items"]

                if new_items and page_token:
                    log.info(f"Processing {len(new_items):,} new message(s)")

                    for item in new_items:
                        message = Message.from_youtube(item, self._stream)
                        await self.events.dispatch(events.MessageCreatedEvent, message)

                page_token = data["nextPageToken"]
                next_poll_in = data["pollingIntervalMillis"] / 1_000
                log.debug(f"Waiting {next_poll_in:,} seconds before next poll")
                await asyncio.sleep(next_poll_in)

            except Exception as exc:
                if isinstance(exc, HTTPError):
                    if 400 <= exc.code <= 499:
                        log.critical("Received 4xx error, cannot continue")
                        return traceback.print_exc()

                log.error(f"Ignoring error during polling (will retry in 5 seconds):")
                traceback.print_exc()
                await asyncio.sleep(5)

    async def send_message(self, content: str) -> Message:
        url = (
            chatto.YOUTUBE_API_BASE_URL
            + f"/liveChat/messages?part=id,snippet,authorDetails"
        )
        data = {
            "snippet": {
                "type": "textMessageEvent",
                "liveChatId": self._stream.chat_id,
                "textMessageDetails": {
                    "messageText": content,
                },
            }
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with self._session.post(url, data=json.dumps(data), headers=headers) as r:
            r.raise_for_status()
            data = await r.json()

        return Message.from_youtube(data, self._stream)

    def run(
        self,
        *,
        read_only: bool = False,
        force_auth: bool = False,
        with_stream_id: str | None = None,
    ) -> None:
        log.info("\33[1mNow starting bot!\33[0m")

        self._loop = asyncio.new_event_loop()

        try:
            # Create session.
            if not self.session:
                # It may have been created during authorisation.
                self._loop.run_until_complete(self.create_session(self._loop))

            # Authorise.
            if not read_only:
                self._loop.run_until_complete(self.authorise(force=force_auth))

            # Fetch stream info.
            self._loop.run_until_complete(self.fetch_stream_info(with_stream_id))

            # Create tasks.
            task = self._loop.create_task(self.poll_for_messages())
            self._loop.create_task(self.events.process())

            # Run loop.
            self._loop.run_until_complete(task)

        except Exception as exc:
            log.critical("A critical error occurred, and Chatto cannot continue")
            raise exc

        except KeyboardInterrupt:
            ...

        finally:
            self.close(self._loop)

    def close(self, loop: AbstractEventLoop) -> None:
        log.debug("Shutting bot down...")

        if self.session:
            loop.run_until_complete(self._session.close())
            log.info("Session closed")

        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
            try:
                log.debug(f"Cancelling task {task}")
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                ...

        loop.close()
        asyncio.set_event_loop(None)
        log.info("Loop closed. See ya later!")
