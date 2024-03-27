from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from requests import Session, Response

class RequestsClient:
    '''
        Facade for Requests library to be compactable with HTTPX client style.

        [TODO]: timeouts
    '''
    def __init__(self, headers: dict, base_url: str, proxies: dict = {}, **kwargs):
        '''
            Init of Requests Client.
        '''
        self.__client: Session = Session()
        self.__base_url = base_url
        self.__proxies = proxies
        self.__main_headers = headers
    
    def get(self, url: str, headers: dict = {}, **kwargs) -> Response:
        '''
            Get request.

            Args: 
            - url: str
            - headers: dict = {}
            - etc. just for not breaking stuff

            Returns:
            - object `requests.Response`
        '''
        return self.__client.get(
            url = self.__base_url + url,
            headers=self.__main_headers | headers,
            proxies=self.__proxies
        )    
    
    def post(self, url: str, headers: dict = {}, data: str | dict | bytes | None = None, **kwargs) -> Response:
        '''
            Post request.

            Args: 
            - url: str
            - headers: dict = {}
            - data: str | dict | bytes | None = None (it will autodetect if its dict and send it as json but not just data)
            - etc. just for not breaking stuff

            Returns:
            - object `requests.Response`
        '''
        return self.__client.post(
            url = self.__base_url + url,
            data=data if not isinstance(data, dict) else None,
            json=data if isinstance(data, dict) else None,
            headers=self.__main_headers | headers,
            proxies=self.__proxies
        )   
    
    def delete(self, url: str, headers: dict = {}, data: str | dict | bytes | None = None, **kwargs) -> Response:
        '''
            Delete request.

            Args: 
            - url: str
            - headers: dict = {}
            - data: str | dict | bytes | None = None (it will autodetect if its dict and send it as json but not just data)
            - etc. just for not breaking stuff

            Returns:
            - object `requests.Response`
        '''
        return self.__client.delete(
            url = self.__base_url + url,
            data=data if not isinstance(data, dict) else None,
            json=data if isinstance(data, dict) else None,
            headers=self.__main_headers | headers,
            proxies=self.__proxies
        )