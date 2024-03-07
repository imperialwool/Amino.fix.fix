# TODO

- generator of user agents (just for fun)
- rewrite sockets (more)
- rotating proxies
- do async using httpx (why need aiohttp when there is httpx installed already)
- subclient -> client (it should be one class where you can set default ndcId, if no ndcId/aminoId it just works like global client, maybe i should also add ndcId parameter to functions that can be executed in global and in community)

## Explaining

- comId SHOULD be ndcId (in amino's code its ndcId, not comId, so i will rename it)
- sockets are spaghetti, i should rewrite them and also add socks proxies support
- httpx is all-in-one solution, its not faster than aiohttp, its a little faster (and convinient) than request. its just comfy all-in-one. if you searching for speedy lib for spaming hacking and blablabla you opened wrong door pretty boy ~
