from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from httpx import Response
from httpx import Timeout as TimeoutConfig
from httpx import Client as HTTPXSYNCCLIENT

class SyncHttpxClient:
    '''
        Facade for HTTPX library. Made for escaping 429.
    '''
    def __init__(
            self,
            headers: dict,
            base_url: str,
            proxies: dict = {},
            timeout: TimeoutConfig | int = 30,
            http2_enabled: bool = False,
            **kwargs
        ):
        '''
            Init of HTTPX Client.
        '''
        self.__proxies = proxies
        self.__timeout = timeout
        self.__base_url = base_url
        self.__main_headers = headers
        self.__http2_enabled = http2_enabled
        self.__client: HTTPXSYNCCLIENT = HTTPXSYNCCLIENT(
            base_url = self.__base_url,
            proxies  = self.__proxies,
            timeout  = self.__timeout,
            headers  = self.__main_headers,
            http2    = self.__http2_enabled,
            follow_redirects = True
        )

    def request(
            self,
            method: str,
            path: str,
            headers: dict = {},
            data: str | bytes | dict | None = None
        ) -> Response:
        '''
            Request.

            Args: 
            - method: str (GET, POST, DELETE, PUT)
            - url: str
            - headers: dict = {}
            - etc. just for not breaking stuff

            Returns:
            - object `httpx.Response`
        '''
        while True:
            r = self.__client.request(
                method  = method,
                url     = path,
                headers = self.__main_headers | headers,
                data    = data
            ) 
            if r.status_code != 429:
                return r
    
    def get(
            self,
            path: str,
            headers: dict = {},
            **kwargs
        ) -> Response:
        '''
            Get request.

            Args: 
            - path: str
            - headers: dict = {}
            - etc. just for not breaking stuff

            Returns:
            - object `httpx.Response`
        '''
        return self.request("GET", path, headers)
    
    def post(
            self,
            path: str,
            headers: dict = {},
            data: str | dict | bytes | None = None,
            **kwargs
        ) -> Response:
        '''
            Post request.

            Args: 
            - path: str
            - headers: dict = {}
            - data: str | dict | bytes | None = None (it will autodetect if its dict and send it as json but not just data)
            - etc. just for not breaking stuff

            Returns:
            - object `httpx.Response`
        '''
        return self.request("POST", path, headers, data)
    
    def delete(
            self,
            path: str,
            headers: dict = {},
            data: str | dict | bytes | None = None,
            **kwargs
        ) -> Response:
        '''
            Delete request.

            Args: 
            - path: str
            - headers: dict = {}
            - data: str | dict | bytes | None = None (it will autodetect if its dict and send it as json but not just data)
            - etc. just for not breaking stuff

            Returns:
            - object `httpx.Response`
        '''
        return self.request("DELETE", path, headers, data)