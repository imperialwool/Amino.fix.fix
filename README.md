# Amino.fix.fix

[![PyPi Version](https://img.shields.io/pypi/v/amino.fix.fix.svg)](https://pypi.python.org/pypi/amino.fix.fix/)
![Python Version](https://img.shields.io/badge/python-%3E%3D3.10-orange)
[![Issues](https://img.shields.io/github/issues-raw/imperialwool/amino.fix.fix.svg?maxAge=25000)](https://github.com/imperialwool/Amino.fix.fix/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/imperialwool/amino.fix.fix.svg?style=flat)](https://github.com/imperialwool/Amino.fix.fix/pulls)

Fork of Amino.fix to improve this library.

## Important notices

- in subclient you should pass `client`, **not** `profile`
- instead of requests this library using **HTTPX**, so if you have issues please [let me know here](https://github.com/imperialwool/Amino.fix.fix/issues/3)
- `lib/util` -> `lib/`
- supporting **only python3.10+***, lower will be never supported
- if you have issues in pydroid, reinstall/update it

## How to install?

`pip install amino.fix.fix`

## How to use it?

If you want to use sync version of library, you should `import aminofixfix`.

If you want to use Async version of library, you should `import aminofixfix.asyncfixfix`.

## API Reference

[Read the Docs Link](https://aminopy.readthedocs.io/en/latest/)

## Asterics

\* So there is things becoming tricky. The *only* reason of python3.10+ badge is officially added `|` between types and None. HTTPX supporting python3.8+, `__future__` solved problems for python3.9x at least. So *maybe* lib is compactable with python3.8+, but I just never tested this and I need your help.
