from .acm import ACM
from .client import Client
from .sub_client import SubClient
from .socket import Callbacks, SocketHandler
from ..lib import exceptions, helpers, objects, headers

from httpx import get
from pkg_resources import parse_version as version

try:
    __newest__ = get("https://pypi.org/pypi/amino.fix.fix/json").json()["info"]["version"]

    if version(__newest__) > version(helpers.LIBRARY_VERSION):
        print("\n!!! New version of amino.fix.fix is available !!!",
            "||| Using: {} | Available: {} |||".format(helpers.LIBRARY_VERSION, __newest__),
            "!!! Please, update library to last version !!!\n", sep="\n")
    elif version(__newest__) < version(helpers.LIBRARY_VERSION):
        print("\n!!! ATTENTION, MODIFIED LIBRARY OR PREVIEW VERSION !!!",
            "||| Using: {} | Available: {} |||".format(helpers.LIBRARY_VERSION, __newest__),
            "!!! Please, make sure that library installed from verified sources !!!",
            "Example: pip install amino.fix.fix\n", sep="\n")
except:
    print("\nCan't check if amino.fix.fix needs update. Please, check internet connection or firewall.\n")