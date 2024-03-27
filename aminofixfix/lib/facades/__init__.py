try:
    from .aiohttp import AiohttpClient, AiohttpResponse
except:
    from .unsuccessful_import import AiohttpClient, AiohttpResponse

try:
    from .requests import RequestsClient
except:
    from .unsuccessful_import import RequestsClient