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

import datetime as dt
import json
import typing as t

import aiofiles
import pytest
from dateutil.tz import tzutc

from chatto.channel import Channel
from chatto.events import EventHandler, MessageCreatedEvent, ReadyEvent
from chatto.message import Message
from chatto.secrets import Secrets
from chatto.stream import Stream
from tests.paths import SECRETS_PATH


@pytest.fixture()  # type: ignore
def channel() -> Channel:
    return Channel(
        id="Ucn978gn48bg984b",
        url="https://youtube.com/mychannel",
        name="Test Channel",
        avatar_url="https://youtube.com/myavatar",
        is_verified=True,
        is_owner=False,
        is_sponsor=True,
        is_moderator=False,
    )


@pytest.fixture()  # type: ignore
def author_details() -> dict[str, t.Any]:
    return {
        "channelId": "Ucn978gn48bg984b",
        "channelUrl": "https://youtube.com/mychannel",
        "displayName": "Test Channel",
        "profileImageUrl": "https://youtube.com/myavatar",
        "isVerified": True,
        "isChatOwner": False,
        "isChatSponsor": True,
        "isChatModerator": False,
    }


@pytest.fixture()  # type: ignore
def secrets() -> Secrets:
    return Secrets.from_file(SECRETS_PATH)


@pytest.fixture()  # type: ignore
def secrets_dict() -> dict[str, t.Any]:
    with open(SECRETS_PATH) as f:
        data = json.load(f)["installed"]

    return t.cast(t.Dict[str, t.Any], data)


@pytest.fixture()  # type: ignore
def stream() -> Stream:
    return Stream(
        id="437n439gn84ng89h430g49bg",
        chat_id="tn389nt9832nbt8932nty80b3982yb",
        start_time=dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=tzutc()),
    )


@pytest.fixture()  # type: ignore
def stream_data() -> dict[str, t.Any]:
    return {
        "id": "437n439gn84ng89h430g49bg",
        "liveStreamingDetails": {
            "actualStartTime": "2022-01-01T00:00:00Z",
            "activeLiveChatId": "tn389nt9832nbt8932nty80b3982yb",
        },
    }


@pytest.fixture()  # type: ignore
def bad_stream_data() -> dict[str, t.Any]:
    return {
        "id": "437n439gn84ng89h430g49bg",
        "liveStreamingDetails": {
            "actualStartTime": "2022-01-01T00:00:00Z",
        },
    }


@pytest.fixture()  # type: ignore
def message(stream: Stream, channel: Channel) -> Message:
    return Message(
        id="r398tn38g8943ng8b40g",
        type="textMessageEvent",
        stream=stream,
        channel=channel,
        published_at=dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=tzutc()),
        content="This is a test!",
    )


@pytest.fixture()  # type: ignore
def youtube_message_data() -> dict[str, t.Any]:
    return {
        "id": "r398tn38g8943ng8b40g",
        "snippet": {
            "type": "textMessageEvent",
            "publishedAt": "2022-01-01T00:00:00.000+00:00",
            "displayMessage": "This is a test!",
        },
        "authorDetails": {
            # Apparently I can't use the fixture here for
            # whatever reason.
            "channelId": "Ucn978gn48bg984b",
            "channelUrl": "https://youtube.com/mychannel",
            "displayName": "Test Channel",
            "profileImageUrl": "https://youtube.com/myavatar",
            "isVerified": True,
            "isChatOwner": False,
            "isChatSponsor": True,
            "isChatModerator": False,
        },
    }


@pytest.fixture()  # type: ignore
def event_handler() -> EventHandler:
    async def ready_cb(event: ReadyEvent) -> None:
        1 / 0

    async def message_cb(event: MessageCreatedEvent) -> None:
        async with aiofiles.open("CALLBACK", "w") as f:
            ...

    e = EventHandler()
    e.subscribe(MessageCreatedEvent, message_cb)
    e.subscribe(ReadyEvent, ready_cb)
    return e
