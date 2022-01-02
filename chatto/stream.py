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

import logging
import typing as t
from dataclasses import dataclass

import chatto
from chatto.errors import ChannelNotLive

if t.TYPE_CHECKING:
    from aiohttp import ClientSession

log = logging.getLogger(__name__)


@dataclass(eq=True, frozen=True)
class Stream:
    id: str
    chat_id: str
    start_time: str

    @classmethod
    async def from_id(
        cls, stream_id: str, token: str, session: ClientSession
    ) -> Stream:
        url = (
            f"{chatto.API_BASE_URL}/{chatto.API_VERSION}/videos"
            f"?key={token}"
            f"&part=liveStreamingDetails"
            f"&id={stream_id}"
        )

        async with session.get(url) as r:
            data = await r.json()

        streaming_details = data["items"][0]["liveStreamingDetails"]
        chat_id = streaming_details.get("activeLiveChatId", None)
        if not chat_id:
            raise ChannelNotLive("no chat ID found -- the stream has probably finished")
        start_time = streaming_details.get("actualStartTime", None)

        log.info("Retrieved chat ID")
        return cls(stream_id, chat_id, start_time)

    @classmethod
    async def from_channel_id(
        cls, channel_id: str, token: str, session: ClientSession
    ) -> Stream:
        url = (
            f"{chatto.API_BASE_URL}/{chatto.API_VERSION}/search"
            f"?key={token}"
            f"&channelId={channel_id}"
            "&eventType=live"
            "&type=video"
        )

        async with session.get(url) as r:
            r.raise_for_status()
            items = (await r.json())["items"]

        if not items:
            raise ChannelNotLive("the provided channel is not live")

        stream_id = items[0]["id"]["videoId"]
        log.info("Retrieved stream ID")
        return await cls.from_id(stream_id, token, session)
