from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from json import loads
from aiohttp import ClientSession, ClientResponse

class AiohttpClient:
    '''
        Facade for aiohttp library to be compactable with HTTPX client style.
        Also made for escaping 429.

        [TODO]: timeouts
    '''
    def __init__(self, headers: dict, base_url: str, proxies: dict | str | None = {}, **kwargs):
        '''
            Init of aiohttp Client.

            If you pass dict as proxies, first proxy in dict will be chosen.
        '''
        self.__proxies = list(proxies.values())[0] if isinstance(proxies, dict) else proxies
        self.__base_url = base_url
        self.__main_headers = headers

        self.__client: ClientSession = ClientSession(
            headers=self.__main_headers
        )

    async def request(
        self,
        method: str,
        url: str,
        headers: dict = {},
        data: str | dict | bytes | None = None,
        **kwargs
    ) -> AiohttpResponse:
        while True:
            async with await self.__client.request(
                method=method,
                url=self.__base_url+url,
                headers=headers,
                data=data,
                ssl=False,
                proxy=self.__proxies
            ) as resp:
                if resp.status not in [429]:
                    answer = AiohttpResponse(resp)
                    await answer._init()
                    return answer
    
    async def get(
        self,
        url: str,
        headers: dict = {},
        **kwargs
    ) -> AiohttpResponse:
        '''
            Get request.

            Args: 
            - url: str
            - headers: dict = {}
            - etc. just for not breaking stuff

            Returns:
            - object `AiohttpResponse`
        '''
        return await self.request("GET", url, headers)  
    
    async def post(self, url: str, headers: dict = {}, data: str | dict | bytes | None = None, **kwargs) -> AiohttpResponse:
        '''
            Post request.

            Args: 
            - url: str
            - headers: dict = {}
            - data: str | dict | bytes | None = None (it will autodetect if its dict and send it as json but not just data)
            - etc. just for not breaking stuff

            Returns:
            - object `AiohttpResponse`
        '''
        return await self.request("POST", url, headers, data)  
    
    async def delete(self, url: str, headers: dict = {}, data: str | dict | bytes | None = None, **kwargs) -> AiohttpResponse:
        '''
            Delete request.

            Args: 
            - url: str
            - headers: dict = {}
            - data: str | dict | bytes | None = None (it will autodetect if its dict and send it as json but not just data)
            - etc. just for not breaking stuff

            Returns:
            - object `AiohttpResponse`
        '''
        return await self.request("DELETE", url, headers, data)  
    
class AiohttpResponse:
    '''
        Facade-response for aiohttp to be compactable with code on HTTPX.
    '''

    def __init__(self, response: ClientResponse):
        self.__response: ClientResponse = response

        self.status_code: int = self.__response.status

    async def _init(self):
        self.content = await self.__response.text()

    def json(self):
        return loads(self.content)
