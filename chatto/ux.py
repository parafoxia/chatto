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

import chatto

BANNER = r"""
    ___       ___       ___       ___       ___       ___
   /\  \     /\__\     /\  \     /\  \     /\  \     /\  \
  /::\  \   /:/__/_   /::\  \    \:\  \    \:\  \   /::\  \
 /:/\:\__\ /::\/\__\ /::\:\__\   /::\__\   /::\__\ /:/\:\__\
 \:\ \/__/ \/\::/  / \/\::/  /  /:/\/__/  /:/\/__/ \:\/:/  /
  \:\__\     /:/  /    /:/  /   \/__/     \/__/     \::/  /
   \/__/     \/__/     \/__/                         \/__/
"""

CLRS = [
    "\33[38;5;1m",
    "\33[38;5;208m",
    "\33[38;5;3m",
    "\33[38;5;2m",
    "\33[38;5;4m",
    "\33[38;5;135m",
]

if t.TYPE_CHECKING:
    HandlersT = list[logging.StreamHandler[t.TextIO] | logging.FileHandler]


def print_banner(extra: str | None = None) -> None:
    banner = ""

    for line in BANNER.splitlines()[1:]:
        for i in range(0, 60, 10):
            banner += CLRS[i // 10] + line[i : i + 10] + "\33[0m"
        banner += "\n"

    if extra:
        banner += f"\n{extra}"
    print(banner)


def display_splash() -> None:
    print_banner()
    print(
        f"A unified API wrapper for \33[1m{CLRS[0]}YouTube\33[0m "
        f"and \33[1m{CLRS[-1]}Twitch\33[0m chat bots.\n\n"
        f"You're using version \33[1m{CLRS[3]}{chatto.__version__}\33[0m.\n\n"
        f"\33[1m{CLRS[2]}Chatto\33[0m is still in alpha, and so may change "
        "(or break) at any time.\n"
        "Keep up with development here: "
        "\33[4mhttps://github.com/parafoxia/chatto\33[0m."
    )


def setup_logging(level: int = logging.INFO, file: str | None = None) -> HandlersT:
    LEVEL = "{levelname[0]}"
    ASCTIME = "\33[38;5;243m{asctime}\33[0m"
    BODY = "{name}: {message}"
    FORMATS = {
        logging.DEBUG: "\33[38;5;246m{}\33[0m",
        logging.INFO: "{}",
        logging.WARNING: "\33[1m\33[38;5;178m{}\33[0m",
        logging.ERROR: "\33[1m\33[38;5;202m{}\33[0m",
        logging.CRITICAL: "\33[1m\33[38;5;196m{}\33[0m",
    }

    class StreamFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            f = FORMATS[record.levelno]
            log_fmt = f"{f.format(LEVEL)}: {ASCTIME}: {f.format(BODY)}"
            formatter = logging.Formatter(log_fmt, style="{", datefmt="%Y-%m-%d %X.%3d")
            return formatter.format(record)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(StreamFormatter())
    handlers: HandlersT = [stream_handler]

    if file:

        class FileFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_fmt = "{levelname[0]}: {asctime}: {name}: {message}"
                formatter = logging.Formatter(
                    log_fmt, style="{", datefmt="%Y-%m-%d %X.%3d"
                )
                return formatter.format(record)

        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(FileFormatter())
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
    )
    return handlers
