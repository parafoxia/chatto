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
import os
import sys

from chatto import events
from chatto.message import Message
from tests.fixtures import *  # noqa


def test_create_handler() -> None:
    handler = events.EventHandler()
    assert isinstance(handler.queue, asyncio.Queue)
    assert handler.callbacks == {}


def test_subscribe_to_event() -> None:
    async def test_cb(event: events.MessageCreatedEvent) -> None:
        ...

    handler = events.EventHandler()
    handler.subscribe(events.MessageCreatedEvent, test_cb)
    assert handler.callbacks == {events.MessageCreatedEvent: [test_cb]}


def test_dispatch_event(message: Message) -> None:
    if sys.version_info >= (3, 10):
        loop = asyncio.new_event_loop()
    else:
        loop = asyncio.get_event_loop()

    handler = events.EventHandler()
    loop.run_until_complete(handler.dispatch(events.MessageCreatedEvent, message))
    assert handler.queue.qsize() == 1

    event = loop.run_until_complete(handler.queue.get())
    assert isinstance(event, events.MessageCreatedEvent)


def test_process_events(event_handler: events.EventHandler, message: Message) -> None:
    if sys.version_info >= (3, 10):
        loop = asyncio.new_event_loop()
    else:
        loop = asyncio.get_event_loop()

    async def kill_on_queue_empty() -> None:
        while True:
            if not event_handler.queue.qsize():
                return

    loop.run_until_complete(event_handler.dispatch(events.MessageCreatedEvent, message))
    killable = loop.create_task(event_handler.process())
    loop.run_until_complete(kill_on_queue_empty())
    killable.cancel()
    try:
        loop.run_until_complete(killable)
    except asyncio.CancelledError:
        ...

    assert os.path.isfile("CALLBACK")


def test_process_bad_events(event_handler: events.EventHandler) -> None:
    if sys.version_info >= (3, 10):
        loop = asyncio.new_event_loop()
    else:
        loop = asyncio.get_event_loop()

    async def kill_on_queue_empty() -> None:
        while True:
            if not event_handler.queue.qsize():
                return

    loop.run_until_complete(event_handler.dispatch(events.ReadyEvent))
    killable = loop.create_task(event_handler.process())
    loop.run_until_complete(kill_on_queue_empty())
    killable.cancel()
    try:
        loop.run_until_complete(killable)
    except asyncio.CancelledError:
        ...
