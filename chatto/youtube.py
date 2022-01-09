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
import pathlib
import sys
import traceback
import typing as t

from aiohttp import ClientSession

import chatto
from chatto import events
from chatto.errors import HTTPError, MissingRequiredInformation, NoSession
from chatto.message import Message
from chatto.oauth import OAuthMixin
from chatto.stream import Stream

if t.TYPE_CHECKING:
    from asyncio.events import AbstractEventLoop

log = logging.getLogger(__name__)


class YouTubeBot(OAuthMixin):
    """A class representing a YouTube bot.

    ## Arguments
    * `api_key` -
        The API key your bot will use.
    * `channel_id` -
        The ID (or seed) of the channel you want your bot to connect to.

    ## Keyword arguments:
    * `secrets_file` -
        The path to your OAuth client secrets file. If this is not
        provided, your OAuth secrets will not be set, and you will not
        be able to authorise your bot. If you want your bot to be able
        to send and delete messages, you will need to provide one.
    * `log_level` -
        The minimum logging level to output information for. To disable
        logging entirely, set this to 0. The default level is INFO.
    * `log_file` -
        The file to save log messages to. If this is not set, Chatto
        will not log to a file.
    """

    __slots__ = (
        "api_key",
        "channel_id",
        "_stream",
        "_loop",
        "_session",
        "_secrets",
        "commands",
        "events",
        "tokens",
    )

    def __init__(
        self,
        api_key: str,
        channel_id: str,
        *,
        secrets_file: pathlib.Path | str | None = None,
        log_level: int = logging.INFO,
        log_file: str | None = None,
    ) -> None:
        chatto.ux.setup_logging(log_level, log_file)
        chatto.ux.print_banner(
            f"Running version \33[1m{chatto.__version__}\33[0m. "
            "Use `\33[1mpython -m chatto\33[0m` for more info.\n"
        )

        self.api_key = api_key
        """The API key the bot will use."""

        if not channel_id:
            raise MissingRequiredInformation("a channel ID must be provided")
        self.channel_id = channel_id
        """The ID of the channel the bot will connect to."""

        self.events = events.EventHandler()
        """The event handler."""

        self.tokens: dict[str, str | int] = {}
        """The OAuth tokens the bot will use."""

        if secrets_file:
            self.use_secrets(secrets_file)

    @property
    def loop(self) -> AbstractEventLoop | None:
        """The asyncio loop the bot is using. If the bot is not running,
        this will be `None`."""
        return getattr(self, "_loop", None)

    @property
    def session(self) -> ClientSession | None:
        """The aiohttp session the bot is using. If the bot is not
        running, this will likely be `None`."""
        return getattr(self, "_session", None)

    @property
    def stream(self) -> Stream | None:
        """The stream the bot is in the live chat for. If the bot is not
        connected to a stream, this will be `None`."""
        return getattr(self, "_stream", None)

    @property
    def authorised(self) -> bool:
        """Whether the bot has been authorised using OAuth."""
        return bool(self.tokens)

    authorized = authorised

    @property
    def access_token(self) -> str | None:
        """The bot's access token. If the bot has not been authorised
        using OAuth, this will be `None`."""
        return self.tokens.get("access_token", None)  # type: ignore

    @property
    def platform(self) -> str:
        """The platform the bot is connected to. This will always be
        "youtube"."""
        return "youtube"

    def listen(
        self, event_type: type[events.Event]
    ) -> t.Callable[[t.Callable[[t.Any], t.Any]], None]:
        """A decorator used to subscribe the wrapped callback to an
        event.

        ## Arguments
        * `event_type` -
            The event type to subscribe to. This **must** be a subclass
            of `events.Event`.

        ## Example
        ```py
        @bot.listen(events.StreamFetchedEvent)
        async def on_stream_fetched(event):
            print(f"Fetched stream with ID: {event.stream.id}")
        ```
        """
        return self.events.listen(event_type)

    async def create_session(self, loop: AbstractEventLoop) -> None:
        """Create a session. This is handled for you.

        ## Arguments
        * `loop` -
            The loop the session should use.
        """
        self._session = ClientSession(loop=loop)
        log.info("New session created")

    async def fetch_stream_info(self, stream_id: str | None = None) -> None:
        """Fetch stream info. This is handled for you.

        ## Arguments
        * `stream_id` -
            The stream ID to fetch information for. If this is not set,
            Chatto will attempt to find the stream using the
            `channel_id`.

        ## Raises
        * `NoSession` -
            There is no active session to use.
        * `HTTPError` -
            An invalid API request was made.
        * `ChannelNotLive` -
            An attempt to get the active stream from a channel that is
            not live was not made. This can sometimes be thrown in
            error, as the YouTube Data API's search endpoint is not 100%
            reliable. See `run` for more information.
        """
        if not self.session:
            raise NoSession("no active session")

        if stream_id:
            self._stream = Stream.from_youtube(
                await Stream.fetch_stream_data(stream_id, self.api_key, self.session)
            )
        else:
            self._stream = Stream.from_youtube(
                await Stream.fetch_active_stream_data(
                    self.channel_id, self.api_key, self.session
                )
            )

        await self.events.dispatch(events.StreamFetchedEvent, self._stream)

    async def make_request(self, url: str) -> dict[str, t.Any]:
        """A helper method for making requests. This should only be used
        for GET requests.

        ## Arguments
        * `url` -
            The URL to make a request to.

        ## Returns
        The data returned by the YouTube API.

        ## Raises
        * `HTTPError` -
            Something is wrong with the request.
        """
        log.debug(f"Making request to {url}")
        async with self._session.get(url) as r:
            data = await r.json()

        err = data.get("error", None)
        if err:
            raise HTTPError(err["code"], err["errors"][0]["message"])

        return data  # type: ignore

    async def poll_for_messages(self) -> None:
        """A forever-looping task that polls the YouTube Live Streaming
        API for new messages. This is handles for you.

        Errors are generally logged and ignored when they occur, except
        for some HTTPErrors.

        ## Raises
        * `HTTPError` -
            An invalid API request was made. This error only
            perpetuates when the status code is between 400 and 499
            inclusive.
        """
        page_token = ""  # nosec: B105 false positive
        url = chatto.YOUTUBE_API_BASE_URL + (
            "/liveChat/messages"
            f"?key={self.api_key}"
            f"&liveChatId={self._stream.chat_id}"
            "&part=snippet,authorDetails"
        )

        while True:
            try:
                log.debug("Polling for new messages...")
                data = await self.make_request(url + f"&pageToken={page_token}")
                await self.events.dispatch(events.ChatPolledEvent, data)
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
        """Send a message to the live chat.

        ## Arguments
        * `content` -
            The message text you want to send.

        ## Returns
        `Message` -
            The message that has been sent.

        ## Raises
        `HTTPError` -
            The API request was invalid.
        """
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
            data = await r.json()

        err = data.get("error", None)
        if err:
            # These ARE the right types -- Mypy just has no idea.
            raise HTTPError(err["code"], err["message"])  # type: ignore

        message = Message.from_youtube(data, self._stream)
        await self.events.dispatch(events.MessageSentEvent, message)
        return message

    def run(
        self,
        *,
        read_only: bool = False,
        force_auth: bool = False,
        with_stream_id: str | None = None,
    ) -> None:
        """Run the bot.

        WARNING:
            This is blocking, and thus should be the last thing you run.

        ## Keyword Arguments
        * `read_only` -
            Whether to launch the bot in read-only mode. You will not be
            able to send or delete messages in this mode, but you will
            also bypass the need to authenticate the bot with OAuth 2.
        * `force_auth` -
            Whether to force OAuth 2 authorisation, irrespective of
            whether existing tokens are available.
        * `with_stream_id` -
            Connectly directly to a specific stream. This is a fallback
            in case the YouTube Data API does not recognise your channel
            is currently live.

        ## Raises
        `Exception` -
            A critical error occurred and Chatto has to shut down.
            Non-critical errors are ignored and logged.
        """
        log.info("\33[1mNow starting bot!\33[0m")

        if sys.version_info >= (3, 10):
            self._loop = asyncio.new_event_loop()
        else:
            self._loop = asyncio.get_event_loop()

        try:
            self._loop.run_until_complete(self.events.create_queue())
            self._loop.run_until_complete(self.create_session(self._loop))

            if not read_only:
                self._loop.run_until_complete(self.authorise(force=force_auth))

            self._loop.run_until_complete(self.fetch_stream_info(with_stream_id))

            task = self._loop.create_task(self.poll_for_messages())
            self._loop.create_task(self.events.process())
            self._loop.create_task(
                self.auto_refresh_tokens(self.tokens["expires_in"])  # type: ignore
            )

            self._loop.run_until_complete(self.events.dispatch(events.ReadyEvent))
            self._loop.run_until_complete(task)

        except Exception as exc:
            log.critical("A critical error occurred, and Chatto cannot continue")
            raise exc

        except KeyboardInterrupt:
            ...

        finally:
            self.close(self._loop)

    def close(self, loop: AbstractEventLoop) -> None:
        """Shut the bot down.

        ## Arguments
        * `loop` -
            The event loop the bot is using.
        """
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
