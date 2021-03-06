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

import asyncio
import json
import typing as t
from pathlib import Path

import pytest

from chatto.secrets import Secrets
from tests.paths import SECRETS_PATH


@pytest.fixture()
def secrets() -> Secrets:
    return Secrets.from_file(SECRETS_PATH)


@pytest.fixture()
def secrets_dict() -> dict[str, t.Any]:
    with open(SECRETS_PATH) as f:
        data = json.load(f)["installed"]

    return t.cast(t.Dict[str, t.Any], data)


def test_load_from_file(secrets_dict: dict[str, t.Any]) -> None:
    secrets = Secrets.from_file(SECRETS_PATH)
    assert secrets.client_id == secrets_dict["client_id"]
    assert secrets.project_id == secrets_dict["project_id"]
    assert secrets.auth_uri == secrets_dict["auth_uri"]
    assert secrets.token_uri == secrets_dict["token_uri"]
    assert (
        secrets.auth_provider_x509_cert_url
        == secrets_dict["auth_provider_x509_cert_url"]
    )
    assert secrets.client_secret == secrets_dict["client_secret"]
    assert secrets.redirect_uris == secrets_dict["redirect_uris"]
    assert secrets.path == SECRETS_PATH


def test_load_from_file_async(secrets_dict: dict[str, t.Any]) -> None:
    secrets = asyncio.run(Secrets.afrom_file(SECRETS_PATH))
    assert secrets.client_id == secrets_dict["client_id"]
    assert secrets.project_id == secrets_dict["project_id"]
    assert secrets.auth_uri == secrets_dict["auth_uri"]
    assert secrets.token_uri == secrets_dict["token_uri"]
    assert (
        secrets.auth_provider_x509_cert_url
        == secrets_dict["auth_provider_x509_cert_url"]
    )
    assert secrets.client_secret == secrets_dict["client_secret"]
    assert secrets.redirect_uris == secrets_dict["redirect_uris"]
    assert secrets.path == SECRETS_PATH


def test_str_output(secrets: Secrets) -> None:
    output = "test-secrets"
    assert str(secrets) == output
    assert f"{secrets}" == output


def test_repr_output(secrets: Secrets) -> None:
    output = (
        "Secrets("
        "client_id='fn497gnwebg9wn98ghw8gh9', "
        "project_id='test-secrets', "
        "auth_uri='https://accounts.google.com/o/oauth2/auth', "
        "token_uri='https://oauth2.googleapis.com/token', "
        "auth_provider_x509_cert_url='https://www.googleapis.com/oauth2/v1/certs', "
        "client_secret='gnfre09gnng094h309gn30bg98', "
        "redirect_uris=['urn:ietf:wg:oauth:2.0:oob', 'http://localhost'], "
        f"path={SECRETS_PATH!r}"
        ")"
    )

    assert repr(secrets) == output
    assert f"{secrets!r}" == output


def test_getattr(secrets: Secrets) -> None:
    assert secrets.client_id == secrets["client_id"]
    assert secrets.project_id == secrets["project_id"]
    assert secrets.auth_uri == secrets["auth_uri"]
    assert secrets.token_uri == secrets["token_uri"]
    assert secrets.auth_provider_x509_cert_url == secrets["auth_provider_x509_cert_url"]
    assert secrets.client_secret == secrets["client_secret"]
    assert secrets.redirect_uris == secrets["redirect_uris"]
    assert secrets.path == secrets["path"]


def test_path_not_path_object() -> None:
    secrets = Secrets.from_file(str(SECRETS_PATH))
    assert isinstance(secrets.path, Path)


def test_file_does_not_exist() -> None:
    with pytest.raises(FileNotFoundError) as exc:
        Secrets.from_file(SECRETS_PATH.parent)
    assert str(exc.value) == "you must provide a valid path to a secrets file"


def test_path_not_path_object_async() -> None:
    secrets = asyncio.run(Secrets.afrom_file(str(SECRETS_PATH)))
    assert isinstance(secrets.path, Path)


def test_file_does_not_exist_async() -> None:
    with pytest.raises(FileNotFoundError) as exc:
        asyncio.run(Secrets.afrom_file(SECRETS_PATH.parent))
    assert str(exc.value) == "you must provide a valid path to a secrets file"


def test_to_dict(secrets: Secrets, secrets_dict: dict[str, t.Any]) -> None:
    assert secrets.to_dict() == secrets_dict
