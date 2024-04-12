# Amino.fix.fix

[![PyPi Version](https://img.shields.io/pypi/v/amino.fix.fix.svg)](https://pypi.python.org/pypi/amino.fix.fix/)
[![PyPi Preview](https://img.shields.io/badge/pypi_pre-v1.0.7b4-blue)](https://pypi.org/project/amino.fix.fix/#history)
![Python Version](https://img.shields.io/badge/python-%3E%3D3.8-orange)
[![Issues](https://img.shields.io/github/issues-raw/imperialwool/amino.fix.fix.svg?maxAge=25000)](https://github.com/imperialwool/Amino.fix.fix/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/imperialwool/amino.fix.fix.svg?style=flat)](https://github.com/imperialwool/Amino.fix.fix/pulls)

Fork of Amino.fix to improve this library.

## Important notices

- in subclient you should pass `client`, **not** `profile`
- if you have issues with HTTPX [let me know here](https://github.com/imperialwool/Amino.fix.fix/issues/3)
- `lib/util` -> `lib/`
- if you have issues in pydroid, reinstall/update it

## How to install?

`pip install amino.fix.fix`

## How to use it?

If you want to use sync version of library, you should `import aminofixfix`.

If you want to use Async version of library, you should `import aminofixfix.asyncfixfix`.

Also instead HTTPX you can use aiohttp, Requests or Urllib3. Just install additional dependencies, if you wanna use them:

- `pip install amino.fix.fix[requests]` # only sync
- `pip install amino.fix.fix[aiohttp]` # only async

Please report any issues and bugs that Request and aiohttp are causing when you use them instead of HTTPX! This feature in beta and not tested well.

Example:

```python
import aminofixfix

client = aminofixfix.Client()
client.login("she.a@lil.freak", "sheforthestreets")

@client.event("on_text_message")
def on_text_message(data):
    if data.message.content == "Six digits on the check, took it to the bank":
        client.send_message(data.message.chatId, "Commas after commas, make ya boy— (Freak out)")

```

## API Reference

[old documentation](https://aminopy.readthedocs.io/en/latest/)

new documentation in progress

## Licenses

- [HTTPX](https://github.com/encode/httpx) is [BSD licensed](https://github.com/encode/httpx/blob/master/LICENSE.md) code. Used as main library to build and send API async and sync requests.
- [Requests](https://github.com/psf/requests) is [Apache 2.0 licensed](https://github.com/psf/requests/blob/main/LICENSE) code. Used as alternative library to build and send API requests.
- [aiohttp](https://github.com/aio-libs/aiohttp) is [Apache 2.0 licensed](https://github.com/aio-libs/aiohttp/blob/master/LICENSE.txt) code. Used as alternative async library to build and send API requests.
- [websocket-client](https://github.com/websocket-client/websocket-client) is [Apache 2.0 licensed](https://github.com/websocket-client/websocket-client/blob/master/LICENSE) code. Used for sockets.
- [python-socks](https://github.com/romis2012/python-socks) is [Apache 2.0 licensed](https://github.com/romis2012/python-socks/blob/master/LICENSE.txt) code. Used for SOCKS proxies in API requests and (in future) sockets.
- [amino.fix](https://github.com/Minori101/Amino.fix) is [MIT licensed](https://github.com/Minori101/Amino.fix/blob/main/LICENSE). Forked to do this library.
- [setuptools](https://github.com/pypa/setuptools) is [MIT licensed](https://github.com/pypa/setuptools/blob/main/LICENSE). Used to build PyPI releases.

This library is [MIT licensed](https://github.com/imperialwool/Amino.fix.fix/blob/main/LICENSE) code.
