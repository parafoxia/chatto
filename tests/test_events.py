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
from asyncio.events import AbstractEventLoop

import aiofiles
import pytest

from chatto import errors, events
from chatto.message import Message
from tests.test_channel import channel
from tests.test_message import message
from tests.test_stream import stream
from tests.test_youtube import loop


@pytest.fixture()
def event_handler() -> events.EventHandler:
    async def ready_cb(event: events.ReadyEvent) -> None:
        1 / 0

    async def message_cb(event: events.MessageCreatedEvent) -> None:
        async with aiofiles.open("CALLBACK", "w") as f:
            ...

    e = events.EventHandler()
    e.subscribe(events.MessageCreatedEvent, message_cb)
    e.subscribe(events.ReadyEvent, ready_cb)
    return e


def test_create_handler() -> None:
    handler = events.EventHandler()
    assert handler.queue == None
    assert handler.callbacks == {}


def test_subscribe_to_event() -> None:
    async def test_cb(event: events.MessageCreatedEvent) -> None:
        ...

    handler = events.EventHandler()
    handler.subscribe(events.MessageCreatedEvent, test_cb)
    assert handler.callbacks == {events.MessageCreatedEvent: [test_cb]}


def test_subscribe_through_decorator() -> None:
    handler = events.EventHandler()

    @handler.listen(events.MessageCreatedEvent)
    async def decorated_test_cb(event: events.MessageCreatedEvent) -> None:
        ...

    # Can't do the same check as before because of the decorator.
    assert len(handler.callbacks) == 1


def test_dispatch_event(message: Message, loop: AbstractEventLoop) -> None:
    handler = events.EventHandler()
    assert handler.queue_size == 0
    loop.run_until_complete(handler.create_queue())
    assert handler.queue_size == 0
    loop.run_until_complete(handler.dispatch(events.MessageCreatedEvent, message))
    assert handler.queue_size == 1

    event = loop.run_until_complete(handler._queue.get())
    assert isinstance(event, events.MessageCreatedEvent)


def test_dispatch_event_without_queue(loop: AbstractEventLoop) -> None:
    handler = events.EventHandler()
    with pytest.raises(errors.NoEventQueue) as exc:
        loop.run_until_complete(handler.dispatch(events.ReadyEvent))
    assert str(exc.value) == "there is no event queue"


def test_process_events(
    event_handler: events.EventHandler, message: Message, loop: AbstractEventLoop
) -> None:
    async def kill_on_queue_empty() -> None:
        while True:
            if not event_handler.queue_size:
                return

    loop.run_until_complete(event_handler.create_queue())
    loop.run_until_complete(event_handler.dispatch(events.MessageCreatedEvent, message))
    killable = loop.create_task(event_handler.process())
    loop.run_until_complete(kill_on_queue_empty())
    loop.run_until_complete(asyncio.sleep(0.5))
    killable.cancel()
    try:
        loop.run_until_complete(killable)
    except asyncio.CancelledError:
        ...

    assert os.path.isfile("CALLBACK")


def test_process_bad_events(
    event_handler: events.EventHandler, loop: AbstractEventLoop
) -> None:
    async def kill_on_queue_empty() -> None:
        while True:
            if not event_handler.queue_size:
                return

    loop.run_until_complete(event_handler.create_queue())
    loop.run_until_complete(event_handler.dispatch(events.ReadyEvent))
    killable = loop.create_task(event_handler.process())
    loop.run_until_complete(kill_on_queue_empty())
    killable.cancel()
    try:
        loop.run_until_complete(killable)
    except asyncio.CancelledError:
        ...


def test_process_events_without_queue(
    event_handler: events.EventHandler, loop: AbstractEventLoop
) -> None:
    with pytest.raises(errors.NoEventQueue) as exc:
        loop.run_until_complete(event_handler.process())
    assert str(exc.value) == "there is no event queue"
