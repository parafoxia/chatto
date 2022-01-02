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
import datetime as dt
import logging
import traceback
import typing as t

from aiohttp import ClientSession

import chatto
from chatto import events
from chatto.errors import ChannelNotLive, HTTPError
from chatto.message import Message

if t.TYPE_CHECKING:
    from asyncio.events import AbstractEventLoop

log = logging.getLogger(__name__)


class YouTubeBot:
    __slots__ = (
        "token",
        "channel_id",
        "stream_id",
        "_loop",
        "_session",
        "_chat_id",
        "commands",
        "events",
    )

    def __init__(
        self,
        token: str,
        channel_id: str,
        stream_id: str | None = None,
        log_level: int = logging.INFO,
        log_file: str | None = None,
    ) -> None:
        chatto.ux.setup_logging(log_level, log_file)
        chatto.ux.print_banner()
        print(
            f"Running version \33[1m{chatto.__version__}\33[0m. "
            "Use `\33[1mpython -m chatto\33[0m` for more info.\n"
        )

        self.token = token
        if not channel_id:
            raise Exception("a channel ID must be provided")
        self.channel_id = channel_id
        self.stream_id = stream_id
        self.events = events.EventHandler()

    @property
    def loop(self) -> AbstractEventLoop | None:
        return getattr(self, "_loop", None)

    @property
    def session(self) -> ClientSession | None:
        return getattr(self, "_session", None)

    @property
    def chat_id(self) -> str | None:
        return getattr(self, "_chat_id", None)

    @property
    def platform(self) -> str:
        return "youtube"

    async def create_session(self, loop: AbstractEventLoop) -> None:
        self._session = ClientSession(loop=loop)
        log.info("New session created")

    async def make_request(self, url: str) -> dict[str, t.Any]:
        log.debug(f"Making request to {url}")
        async with self._session.get(url) as r:
            log.debug(f"Request: {r}")
            data = await r.json()

        err = data.get("error", None)
        if err:
            raise HTTPError(err["code"], err["errors"][0]["message"])

        return t.cast(dict[str, t.Any], data)

    async def set_active_chat_id(self) -> None:
        async def fetch_current_stream() -> str:
            log.info("No stream ID provided -- searching for active one...")
            url = (
                f"{chatto.API_BASE_URL}/{chatto.API_VERSION}/search"
                f"?key={self.token}"
                f"&channelId={self.channel_id}"
                "&eventType=live"
                "&type=video"
            )

            data = await self.make_request(url)
            items = data["items"]

            if not items:
                raise ChannelNotLive("the provided channel is not live")

            stream_id = items[0]["id"]["videoId"]
            log.info(f"Found active stream! ({stream_id})")
            return t.cast(str, stream_id)

        log.info("Fetching chat ID...")
        url = (
            f"{chatto.API_BASE_URL}/{chatto.API_VERSION}/videos"
            f"?key={self.token}"
            f"&part=liveStreamingDetails"
            f"&id={self.stream_id or await fetch_current_stream()}"
        )

        data = await self.make_request(url)
        self._chat_id = data["items"][0]["liveStreamingDetails"].get(
            "activeLiveChatId", None
        )
        if not self._chat_id:
            raise ChannelNotLive("no chat ID found -- the stream has probably finished")

        log.info(f"Chatto is ready to receive messages!")
        await self.events.push(events.ReadyEvent)

    async def poll_for_messages(self) -> None:
        def is_new(item: dict[str, t.Any]) -> bool:
            published = item["snippet"]["publishedAt"]
            if published <= last_received:
                return False
            return True

        url = (
            f"{chatto.API_BASE_URL}/{chatto.API_VERSION}/liveChat/messages"
            f"?key={self.token}"
            f"&liveChatId={self.chat_id}"
            "&part=id,snippet,authorDetails"
        )
        last_received = dt.datetime.utcnow().isoformat()

        while True:
            try:
                log.debug("Polling for new messages...")
                data = await self.make_request(url)
                new_items = tuple(filter(is_new, data["items"]))

                if new_items:
                    log.info(f"Processing {len(new_items):,} new messages")

                    for item in new_items:
                        msg = Message.from_youtube(item)
                        await self.events.push(events.MessageCreateEvent, msg)

                    last_received = new_items[-1]["snippet"]["publishedAt"]

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

    def run(self) -> None:
        log.info("NOW STARTING BOT")

        self._loop = asyncio.new_event_loop()

        try:
            # Get attributes.
            self._loop.run_until_complete(self.create_session(self._loop))
            self._loop.run_until_complete(self.set_active_chat_id())

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
