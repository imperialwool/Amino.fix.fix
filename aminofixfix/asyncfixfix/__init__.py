from .acm import ACM
from .client import Client
from .sub_client import SubClient
from .socket import Callbacks, SocketHandler
from ..lib import exceptions, helpers, objects, headers

from json import loads
from threading import Thread
from urllib.request import urlopen
from pkg_resources import parse_version as version

def work():
    try:
        response = urlopen("https://pypi.org/pypi/amino.fix.fix/json")
        data = loads(response.read())

        __newest__ = data["info"]["version"]

        if version(__newest__) > version(helpers.LIBRARY_VERSION):
            print(
                "\n! New version of amino.fix.fix is available !",
                "| Using: {} | Available: {} |\n".format(helpers.LIBRARY_VERSION, __newest__),
                
                sep="\n"
            )
        elif version(__newest__) < version(helpers.LIBRARY_VERSION):
            print(
                "\n! Using preview version {} of amino.fix.fix !".format(helpers.LIBRARY_VERSION),
                "| Latest stable available: {} |\n".format(__newest__),
                
                sep="\n"
            )
    except:
        print("\nCan't check if amino.fix.fix needs update. Please, check internet connection or firewall.\n")

Thread(target=work).start()