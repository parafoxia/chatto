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

import asyncio
from asyncio.events import AbstractEventLoop

import pytest
from aiohttp.client import ClientSession

from chatto import errors, events
from chatto.secrets import Secrets
from chatto.youtube import YouTubeBot
from tests.paths import SECRETS_PATH
from tests.test_secrets import secrets


@pytest.fixture()
def loop() -> AbstractEventLoop:
    # This has to use new even in < Python 3.10.
    return asyncio.new_event_loop()


@pytest.fixture()
def youtube_bot() -> YouTubeBot:
    return YouTubeBot(
        "riuebg0843b9g8n4gb8493",
        "f84ng0409gj490gh43809gh",
    )


@pytest.fixture()
def authed_youtube_bot() -> YouTubeBot:
    return YouTubeBot(
        "riuebg0843b9g8n4gb8493",
        "f84ng0409gj490gh43809gh",
        secrets_file=SECRETS_PATH,
    )


def test_create_youtube_bot(youtube_bot: YouTubeBot) -> None:
    assert youtube_bot.token == "riuebg0843b9g8n4gb8493"
    assert youtube_bot.channel_id == "f84ng0409gj490gh43809gh"


def test_create_authed_youtube_bot(
    authed_youtube_bot: YouTubeBot, secrets: Secrets
) -> None:
    assert authed_youtube_bot.token == "riuebg0843b9g8n4gb8493"
    assert authed_youtube_bot.channel_id == "f84ng0409gj490gh43809gh"
    assert authed_youtube_bot._secrets == secrets


def test_create_youtube_bot_no_channel_id() -> None:
    with pytest.raises(errors.MissingRequiredInformation) as exc:
        YouTubeBot("token", "")
    assert str(exc.value) == "a channel ID must be provided"


def test_properties_on_creation(youtube_bot: YouTubeBot) -> None:
    assert not youtube_bot.loop
    assert not youtube_bot.session
    assert not youtube_bot.stream
    assert not youtube_bot.authorised
    assert not youtube_bot.authorized
    assert not youtube_bot.access_token
    assert youtube_bot.platform == "youtube"


def test_listen_decorator(youtube_bot: YouTubeBot) -> None:
    assert youtube_bot.events.callbacks == {}

    @youtube_bot.listen(events.MessageCreatedEvent)
    async def youtube_cb(event: events.MessageCreatedEvent) -> None:
        ...

    assert len(youtube_bot.events.callbacks) == 1


def test_create_session(youtube_bot: YouTubeBot, loop: AbstractEventLoop) -> None:
    loop.run_until_complete(youtube_bot.create_session(loop))
    assert isinstance(youtube_bot._session, ClientSession)
    assert youtube_bot.session == youtube_bot._session
