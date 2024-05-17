try:
    from .aiohttp import AiohttpClient, AiohttpResponse
except:
    from .unsuccessful_import import AiohttpClient, AiohttpResponse

try:
    from .requests import RequestsClient
except:
    from .unsuccessful_import import RequestsClient

try:
    from .sync_httpx import SyncHttpxClient
except:
    from .unsuccessful_import import SyncHttpxClient

try:
    from .async_httpx import AsyncHttpxClient
except:
    from .unsuccessful_import import AsyncHttpxClient