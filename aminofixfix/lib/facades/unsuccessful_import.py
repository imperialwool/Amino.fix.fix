HTTPX_TEXT = "You need to install HTTPX.\nBest way to do this without breaking anything, type this command:\npip install amino.fix.fix"
AIOHTTP_TEXT = "You need to install aiohttp.\nBest way to do this without breaking anything, type this command:\npip install amino.fix.fix[aiohttp]"
REQUESTS_TEXT = "You need to install requests.\nBest way to do this without breaking anything, type this command:\npip install amino.fix.fix[requests]"

class AiohttpClient:
    def __init__(self, **kwargs):
        raise Exception(AIOHTTP_TEXT)
    
class AiohttpResponse:
    def __init__(self, **kwargs):
        raise Exception(AIOHTTP_TEXT)

class RequestsClient:
    def __init__(self, **kwargs):
        raise Exception(REQUESTS_TEXT)

class SyncHttpxClient:
    def __init__(self, **kwargs):
        raise Exception(HTTPX_TEXT)
    
class AsyncHttpxClient:
    def __init__(self, **kwargs):
        raise Exception(HTTPX_TEXT)