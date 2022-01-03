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
import logging
import typing as t
from dataclasses import dataclass

from dateutil.parser import parse as parse_ts

import chatto
from chatto.errors import ChannelNotLive, HTTPError

if t.TYPE_CHECKING:
    from aiohttp import ClientSession

log = logging.getLogger(__name__)


@dataclass(eq=True, frozen=True)
class Stream:
    id: str
    chat_id: str
    start_time: dt.datetime

    @classmethod
    async def from_id(
        cls, stream_id: str, token: str, session: ClientSession
    ) -> Stream:
        url = chatto.YOUTUBE_API_BASE_URL + (
            f"/videos?key={token}&part=liveStreamingDetails&id={stream_id}"
        )

        async with session.get(url) as r:
            data = await r.json()

        err = data.get("error", None)
        if err:
            raise HTTPError(err["code"], err["errors"][0]["message"])

        streaming_details = data["items"][0]["liveStreamingDetails"]
        chat_id = streaming_details.get("activeLiveChatId", None)
        if not chat_id:
            raise ChannelNotLive("the stream has no active chat ID")
        start_time = parse_ts(streaming_details["actualStartTime"])

        log.info(f"Retrieved stream info for stream {stream_id}")
        return cls(stream_id, chat_id, start_time)

    @classmethod
    async def from_channel_id(
        cls, channel_id: str, token: str, session: ClientSession
    ) -> Stream:
        url = chatto.YOUTUBE_API_BASE_URL + (
            "/search"
            f"?key={token}"
            f"&channelId={channel_id}"
            "&eventType=live"
            "&type=video"
        )

        async with session.get(url) as r:
            data = await r.json()

        err = data.get("error", None)
        if err:
            raise HTTPError(err["code"], err["errors"][0]["message"])

        items = data["items"]

        if not items:
            raise ChannelNotLive("the provided channel is not live")

        stream_id = items[0]["id"]["videoId"]
        log.info(f"Retrieved ID of currently live stream ({stream_id})")
        return await cls.from_id(stream_id, token, session)
