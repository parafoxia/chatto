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
import enum

import datetime as dt
import typing as t
from dataclasses import dataclass

from dateutil.parser import parse as parse_ts

from chatto.channel import Channel
from chatto.stream import Stream

class MessageTypes(enum.Enum):
    ChatEndedEvent = "chatEndedEvent"
    MessageDeletedEvent = "messageDeletedEvent" 
    NewSponsorEvent = "newSponsorEvent"
    SponsorOnlyModeEndedEvent = "sponsorOnlyModeEndedEvent"
    SponsorOnlyModeStartedEvent = "sponsorOnlyModeStartedEvent"
    MemberMilestoneChatEvent = "memberMilestoneChatEvent"
    SuperChatEvent = "superChatEvent"
    SuperStickerEvent = "superStickerEvent"
    TextMessageEvent = "textMessageEvent"
    Tombstone = "tombstone"
    UserBannedEvent = "userBannedEvent"

@dataclass(eq=True, frozen=True)
class Message:
    id: str
    type: MessageTypes
    stream: Stream
    channel: Channel
    published_at: dt.datetime
    content: str

    def get_type(type: str) -> MessageTypes:
        print(type == MessageTypes.TextMessageEvent.value)
        if (type == MessageTypes.ChatEndedEvent.value): return MessageTypes.ChatEndedEvent
        if (type == MessageTypes.MessageDeletedEvent.value): return MessageTypes.MessageDeletedEvent
        if (type == MessageTypes.NewSponsorEvent.value): return MessageTypes.NewSponsorEvent
        if (type == MessageTypes.SponsorOnlyModeEndedEvent.value): return MessageTypes.SponsorOnlyModeEndedEvent
        if (type == MessageTypes.SponsorOnlyModeStartedEvent.value): return MessageTypes.SponsorOnlyModeStartedEvent
        if (type == MessageTypes.MemberMilestoneChatEvent.value): return MessageTypes.MemberMilestoneChatEvent
        if (type == MessageTypes.SuperChatEvent.value): return MessageTypes.SuperChatEvent
        if (type == MessageTypes.SuperStickerEvent.value): return MessageTypes.SuperStickerEvent
        if (type == MessageTypes.TextMessageEvent.value): return MessageTypes.TextMessageEvent
        if (type == MessageTypes.Tombstone.value): return MessageTypes.Tombstone
        if (type == MessageTypes.UserBannedEvent.value): return MessageTypes.UserBannedEvent

    @classmethod
    def from_youtube(cls, item: dict[str, t.Any], stream: Stream) -> Message:
        snippet = item["snippet"]
        return cls(
            id=item["id"],
            type=cls.get_type(snippet["type"]),
            stream=stream,
            channel=Channel.from_author(item["authorDetails"]),
            published_at=parse_ts(snippet["publishedAt"]),
            content=snippet["displayMessage"],
        )
