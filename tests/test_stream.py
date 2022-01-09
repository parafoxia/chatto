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

from chatto import errors
from chatto.stream import Stream


@pytest.fixture()
def stream() -> Stream:
    return Stream(
        id="437n439gn84ng89h430g49bg",
        chat_id="tn389nt9832nbt8932nty80b3982yb",
        start_time=dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=tzutc()),
    )


@pytest.fixture()
def stream_data() -> dict[str, t.Any]:
    return {
        "id": "437n439gn84ng89h430g49bg",
        "liveStreamingDetails": {
            "actualStartTime": "2022-01-01T00:00:00Z",
            "activeLiveChatId": "tn389nt9832nbt8932nty80b3982yb",
        },
    }


@pytest.fixture()
def bad_stream_data() -> dict[str, t.Any]:
    return {
        "id": "437n439gn84ng89h430g49bg",
        "liveStreamingDetails": {
            "actualStartTime": "2022-01-01T00:00:00Z",
        },
    }


def test_create_stream(stream: Stream) -> None:
    assert stream.id == "437n439gn84ng89h430g49bg"
    assert stream.chat_id == "tn389nt9832nbt8932nty80b3982yb"
    assert stream.start_time == dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=tzutc())


def test_create_stream_from_data(stream: Stream, stream_data: dict[str, t.Any]) -> None:
    assert stream == Stream.from_youtube(stream_data)


def test_create_stream_from_bad_data(
    stream: Stream, bad_stream_data: dict[str, t.Any]
) -> None:
    with pytest.raises(errors.ChannelNotLive) as exc:
        assert stream == Stream.from_youtube(bad_stream_data)
    assert str(exc.value) == "the stream has no active chat ID"
