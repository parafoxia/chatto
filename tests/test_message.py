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
import typing as t

import pytest
from dateutil.tz import tzutc

from chatto.channel import Channel
from chatto.message import Message
from chatto.stream import Stream
from tests.test_channel import channel
from tests.test_stream import stream


@pytest.fixture()
def message(stream: Stream, channel: Channel) -> Message:
    return Message(
        id="r398tn38g8943ng8b40g",
        type="textMessageEvent",
        stream=stream,
        channel=channel,
        published_at=dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=tzutc()),
        content="This is a test!",
    )


@pytest.fixture()
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


def test_create_message(message: Message, stream: Stream, channel: Channel) -> None:
    assert message.id == "r398tn38g8943ng8b40g"
    assert message.type == "textMessageEvent"
    assert message.stream == stream
    assert message.channel == channel
    assert message.published_at == dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=tzutc())
    assert message.content == "This is a test!"


def test_create_from_youtube_data(
    message: Message, youtube_message_data: dict[str, t.Any], stream: Stream
) -> None:
    assert message == Message.from_youtube(youtube_message_data, stream)
