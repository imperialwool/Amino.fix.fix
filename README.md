# Amino.fix.fix

[![PyPi Version](https://img.shields.io/pypi/v/amino.fix.fix.svg)](https://pypi.python.org/pypi/amino.fix.fix/)
![PyPi Preview](https://img.shields.io/badge/pypi_pre-v1.0.5b6-blue)
![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-orange)
[![Issues](https://img.shields.io/github/issues-raw/imperialwool/amino.fix.fix.svg?maxAge=25000)](https://github.com/imperialwool/Amino.fix.fix/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/imperialwool/amino.fix.fix.svg?style=flat)](https://github.com/imperialwool/Amino.fix.fix/pulls)

Fork of Amino.fix to improve this library.

## Important notices

- in subclient you should pass `client`, **not** `profile`
- instead of requests this library using **HTTPX**, so if you have issues please [let me know here](https://github.com/imperialwool/Amino.fix.fix/issues/3)
- `lib/util` -> `lib/`
- supporting **only python3.9+**¹, maybe 3.8+, lower will be never supported
- if you have issues in pydroid, reinstall/update it

## How to install?

`pip install amino.fix.fix`

## How to use it?

If you want to use sync version of library, you should `import aminofixfix`.

If you want to use Async version of library, you should `import aminofixfix.asyncfixfix`.

## API Reference

[Read the Docs Link](https://aminopy.readthedocs.io/en/latest/)

## Licenses

- [HTTPX](https://github.com/encode/httpx) is [BSD licensed](https://github.com/encode/httpx/blob/master/LICENSE.md) code. Used for building client for API requests.
- [websocket-client](https://github.com/websocket-client/websocket-client) is [Apache 2.0 licensed](https://github.com/websocket-client/websocket-client/blob/master/LICENSE) code. Used for sockets.
- [python-socks](https://github.com/romis2012/python-socks) is [Apache 2.0 licensed](https://github.com/romis2012/python-socks/blob/master/LICENSE.txt) code. Used for SOCKS proxies in API requests and (in future) sockets.
- [amino.fix](https://github.com/Minori101/Amino.fix) is [MIT licensed](https://github.com/Minori101/Amino.fix/blob/main/LICENSE). Forked to do this library.
- [setuptools](https://github.com/pypa/setuptools) is [MIT licensed](https://github.com/pypa/setuptools/blob/main/LICENSE). Used to build PyPI releases.

This library is [MIT licensed](https://github.com/imperialwool/Amino.fix.fix/blob/main/LICENSE) code.

## Astericks

¹ So there is things becoming tricky. Python3.10 officially added `|` between types and None. HTTPX supporting python3.8+, `__future__` solved problems for python3.9x at least (i tested). So *maybe* lib is compactable with python3.8+, but I just never tested this and I need your help.
