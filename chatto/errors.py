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


class ChattoError(Exception):
    """The base exception class for Chatto."""


class HTTPError(ChattoError):
    """Exception thrown when API requests return errors.

    ## Arguments
    * code (`int`):
        The status code of the error.
    * body (`str`):
        The error message.
    """

    def __init__(self, code: int, body: str) -> None:
        super().__init__(f"{code}: {body}")
        self.code = code
        """The status code of the error."""

        self.body = body
        """The error message."""


class ChannelNotLive(ChattoError):
    """Exception thrown when the specified channel is not live when the
    bot attempts to run."""


class NoSession(ChattoError):
    """Exception thrown when attempting to perform an action that
    requires a session, but it has not been made."""


class NoEventQueue(ChattoError):
    """Exception thrown when attempting to perform an action that
    requires an event queue, but it has not been made."""


class MissingRequiredInformation(ChattoError):
    """Exception thrown when insufficient information has been provided
    to perform the required task."""


class NoSecrets(ChattoError):
    """Exception thrown when attempting to perform an action that
    requires OAuth secrets, but they have not been set."""


class NotAuthorised(ChattoError):
    """Exception thrown when attempting to perform an action that
    requires OAuth authentication, but it has not been done."""
