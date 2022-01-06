# Chatto

[![PyPi version](https://img.shields.io/pypi/v/chatto.svg)](https://pypi.python.org/pypi/chatto/)
[![Downloads](https://pepy.tech/badge/chatto)](https://pepy.tech/project/chatto)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/parafoxia/chatto/CI?label=ci)](https://github.com/parafoxia/chatto/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/parafoxia/chatto.svg)](https://github.com/parafoxia/chatto/blob/main/LICENSE)

A unified API wrapper for YouTube and Twitch chat bots.

CPython versions 3.8 through 3.10 and PyPy version 3.8 are officially supported.

Windows, MacOS, and Linux are all supported.

## Installation

To install the latest stable version of *Chatto*:

```sh
pip install chatto

# If you need types:
pip install "chatto[types]"
```

To install the latest development version:

```sh
pip install git+https://github.com/parafoxia/chatto
```

You may need to prefix these commands with a call to the Python interpreter depending on your OS and Python configuration.

## Setup

Before you begin, you will need to have a Google Developers project with the YouTube Data API V3 enabled. You need an API key, and if you want to send and delete messages, you will need an OAuth client ID.

Although this project is currently undocumented, I [made a video](https://www.youtube.com/watch?v=1Xday10ZWeg) walking through all the necessary steps.

## Creating a YouTube bot

To create a simple YouTube bot, you could do something like this:

```py
import os

from chatto import YouTubeBot
from chatto.events import MessageCreatedEvent

bot = YouTubeBot(
    # Your project's API key.
    os.environ["API_KEY"],
    # The ID of the channel whose stream you want to connect to.
    os.environ["CHANNEL_ID"],
    # Your OAuth client ID secrets file.
    secrets_file="secrets.json",
)


# Listen for MessageCreatedEvents, and run this awaitable whenever a
# new message is received.
@bot.listen(MessageCreatedEvent)
async def on_message_created(event):
    # Ignore messages sent by the broadcaster.
    if event.message.channel.is_owner:
        return

    # Respond to messages starting with "!hello".
    if event.message.content.startswith("!hello"):
        await bot.send_message(f"Hi {event.message.channel.name}!")


if __name__ == "__main__":
    # This is blocking, so should be the last thing you call.
    bot.run()
```

Chatto relies on the `/search` endpoint to find a live broadcast from a channel, which is not 100% reliable. If you are having major issues getting Chatto to find your channel's live stream, you can pass the stream ID directly:

```py
bot.run(with_stream_id=os.environ["STREAM_ID"])
```

If you don't want to use OAuth, you can launch Chatto in read-only mode. Note that your bot will not be able to send or delete messages in this mode:

```py
bot.run(read_only=True)
```

## Creating a Twitch bot

Twitch bots are not yet supported.

## Contributing

Contributions are very much welcome! To get started:

* Familiarise yourself with the [code of conduct](https://github.com/parafoxia/chatto/blob/main/CODE_OF_CONDUCT.md)
* Have a look at the [contributing guide](https://github.com/parafoxia/chatto/blob/main/CONTRIBUTING.md)

## License

The *Chatto* module for Python is licensed under the [BSD 3-Clause License](https://github.com/parafoxia/chatto/blob/main/LICENSE).
