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

import re

from chatto import oauth
from chatto.secrets import Secrets
from tests.test_secrets import secrets  # noqa

STATE_PATTERN = re.compile("[0-9a-f]{64}")


def test_create_state() -> None:
    assert STATE_PATTERN.match(oauth.create_state())


def test_get_auth_uri(secrets: Secrets) -> None:
    url, state = oauth.get_auth_url(secrets)

    assert url == (
        "https://accounts.google.com/o/oauth2/auth"
        "?response_type=code"
        "&client_id=fn497gnwebg9wn98ghw8gh9"
        "&redirect_uri=urn:ietf:wg:oauth:2.0:oob"
        "&scope=https://www.googleapis.com/auth/youtube"
        f"&state={state}"
    )
    assert STATE_PATTERN.match(state)


def test_get_token_request_data(secrets: Secrets) -> None:
    code = "4ng0843ng89n340gn4028ng084n"
    data, headers = oauth.get_token_request_data(code, secrets=secrets)

    assert data == {
        "client_id": "fn497gnwebg9wn98ghw8gh9",
        "client_secret": "gnfre09gnng094h309gn30bg98",
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    }
    assert headers == {"Content-Type": "application/x-www-form-urlencoded"}
