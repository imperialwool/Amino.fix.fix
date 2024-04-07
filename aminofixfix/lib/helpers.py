from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from base64 import b64decode, b64encode
from time import timezone as tz_raw
from time import time as timestamp
from functools import reduce
from random import choice
from hashlib import sha1
from os import urandom
from json import loads
from uuid import uuid4
from hmac import new
import re

LIBRARY_VERSION = "1.0.7b4"

PREFIX = bytes.fromhex("19")
SIG_KEY = bytes.fromhex("DFA5ED192DDA6E88A12FE12130DC6206B1251E44")
DEVICE_KEY = bytes.fromhex("E7309ECC0953C6FA60005B2765F99DBBC965C8E9")

IPHONE_IDS = [
    "11,2", "11,4", "11,6", "11,8",
    "12,1", "12,3", "12,5", "12,8",
    "13,1", "13,2", "13,3", "13,4",
    "14,2", "14,3", "14,4", "14,5", "14,6", "14,7", "14,8",
    "15,2", "15,3", "15,4", "15,5",
    "16,1", "16,2"
]
IOS_VERSIONS = [
    "14.2", "14.3", "14.4", "14.4.1", "14.4.2", "14.5", "14.5.1", "14.6", "14.7", "14.7.1", "14.8", "14.8.1",
    "15.0", "15.0.1", "15.0.2", "15.1", "15.1.1", "15.2", "15.2.1", "15.3", "15.3.1", "15.4", "15.4.1", "15.5", "15.6", "15.6.1", "15.7", "15.7.1",
    "16.0", "16.0.2", "16.0.3", "16.1", "16.1.1", "16.1.2", "16.2", "16.3", "16.3.1", "16.4", "16.4.1", "16.5", "16.5.1", "16.6", "16.6.1", "16.7", "16.7.1", "16.7.2",
    "17.0", "17.0.1", "17.0.2", "17.0.3", "17.1", "17.1.1", "17.1.2", "17.2", "17.2.1", "17.3", "17.3.1", "17.4"
]
APP_VERSIONS = [
    "3.23.0", "3.22.0", "3.21.0", "3.20.0"
]

LOCAL_TIMEZONE = -tz_raw // 1000

def str_uuid4() -> str: return str(uuid4())

def inttime() -> int: return int(timestamp() * 1000)
def clientrefid() -> int: return int(timestamp() / 10 % 1000000000)

def b64_to_bytes(b64: str) -> str: b64decode(b64).decode()
def bytes_to_b64(data: bytes) -> str: b64encode(data).decode()

def gen_deviceId(data: bytes = None) -> str:
    identifier = PREFIX + ((data if isinstance(data, bytes) else bytes(data, 'utf-8')) if data else urandom(20))
    return "{}{}".format(identifier.hex(), new(DEVICE_KEY, identifier, sha1).hexdigest()).upper()

def gen_userAgent() -> str:
    return "Apple iPhone{} iOS v{} Main/{}".format(
        choice(IPHONE_IDS), choice(IOS_VERSIONS), choice(APP_VERSIONS)
    )

def signature(data: str | bytes) -> str:
    data = data if isinstance(data, bytes) else data.encode("utf-8")
    return b64encode(PREFIX + new(SIG_KEY, data, sha1).digest()).decode("utf-8")

def update_deviceId(device: str) -> str:
    return gen_deviceId(bytes.fromhex(device[2:42]))

def decode_sid(sid: str) -> dict:
    return loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]

def json_minify(string, strip_space=True):
    '''
        Took from: https://github.com/getify/JSON.minify/tree/python
        Library under MIT license.
        
        I think install library to just minify json is stupid,
        so I copied function, sorry.
    '''
    tokenizer = re.compile(r'"|(/\*)|(\*/)|(//)|\n|\r')
    end_slashes_re = re.compile(r'(\\)*$')

    in_string = False
    in_multi = False
    in_single = False

    new_str = []
    index = 0

    for match in re.finditer(tokenizer, string):

        if not (in_multi or in_single):
            tmp = string[index:match.start()]
            if not in_string and strip_space:
                # replace white space as defined in standard
                tmp = re.sub('[ \t\n\r]+', '', tmp)
            new_str.append(tmp)
        elif not strip_space:
            # Replace comments with white space so that the JSON parser reports
            # the correct column numbers on parsing errors.
            new_str.append(' ' * (match.start() - index))

        last_index = index
        index = match.end()
        val = match.group()

        if val == '"' and not (in_multi or in_single):
            escaped = end_slashes_re.search(string, last_index, match.start())

            # start of string or unescaped quote character to end string
            if not in_string or (escaped is None or len(escaped.group()) % 2 == 0):  # noqa
                in_string = not in_string
            index -= 1  # include " character in next catch
        elif not (in_string or in_multi or in_single):
            if val == '/*':
                in_multi = True
            elif val == '//':
                in_single = True
        elif val == '*/' and in_multi and not (in_string or in_single):
            in_multi = False
            if not strip_space:
                new_str.append(' ' * len(val))
        elif val in '\r\n' and not (in_multi or in_string) and in_single:
            in_single = False
        elif not ((in_multi or in_single) or (val in ' \r\n\t' and strip_space)):  # noqa
            new_str.append(val)

        if not strip_space:
            if val in '\r\n':
                new_str.append(val)
            elif in_multi or in_single:
                new_str.append(' ' * len(val))

    new_str.append(string[index:])
    return ''.join(new_str)