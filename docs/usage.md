Usage
=====

Installation
------------

To use Amino.fix.fix, first install it using pip:

```console
(.venv) $ pip install amino.fix.fix
```

Also if you don't like HTTPX version, you can install Requests and/or aiohttp versions
of library and choose Requests, aiohttp or HTTPX in Client.

```console
(.venv) $ pip install amino.fix.fix[aiohttp]
(.venv) $ pip install amino.fix.fix[requests]
```

Library works on Windows, Linux, macOS, Android (Termux, Pydroid3) and even iOS
(tested on iOS 16.5 with Dopamine and python3.9 compiled by procursus).

Basic usage
----------------

```python
import aminofixfix

client = aminofixfix.Client()
client.login("she.a@lil.freak", "sheforthestreets")

@client.event("on_text_message")
def on_text_message(data):
    if data.message.content == "Six digits on the check, took it to the bank":
        client.send_message(data.message.chatId, "Commas after commas, make ya boy— (Freak out)")
```
