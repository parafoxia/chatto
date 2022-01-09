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

import typing as t
from dataclasses import dataclass


@dataclass
class Channel:
    """A dataclass representing a channel. All class variables are also
    parameters that should be passed into the constructor."""

    id: str
    """The channel ID."""

    url: str
    """The URL of the channel."""

    name: str
    """The display name of the channel."""

    avatar_url: str
    """The URL of the channel's avatar."""

    is_verified: bool
    """Whether the channel's identity has been verified by YouTube."""

    is_owner: bool
    """Whether the channel is the owner of the live chat."""

    is_sponsor: bool
    """Whether the channel is a sponsor of the live chat."""

    is_moderator: bool
    """Whether the channel is a moderator of the live chat."""

    @classmethod
    def from_author(cls, data: dict[str, t.Any]) -> Channel:
        """Create a `Channel` object from the author details of a
        liveChatMessage resource from the YouTube Live Streaming API.

        ## Arguments
        * `data` -
            The author details from the liveChatMessage resource.

        ## Returns
        * `Channel` -
            The newly created channel object.
        """
        return cls(
            id=data["channelId"],
            url=data["channelUrl"],
            name=data["displayName"],
            avatar_url=data["profileImageUrl"],
            is_verified=data["isVerified"],
            is_owner=data["isChatOwner"],
            is_sponsor=data["isChatSponsor"],
            is_moderator=data["isChatModerator"],
        )
