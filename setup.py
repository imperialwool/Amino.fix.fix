from setuptools import setup, find_packages

requirements = [
    "httpx",
    "httpx[http2]",
    "httpx[socks]",
    "websocket-client==1.3.1", 
    "setuptools", 
    "json_minify"
]

setup(
    name="amino.fix.fix",
    license="MIT",
    author="imperialwool",
    version="1.0",
    author_email="hi@iwool.dev",
    description="Library for Aminoapps",
    url="https://github.com/imperialwool/Amino.fix.fix",
    packages=find_packages(),
    long_description=open("README.md").read(),
    install_requires=requirements,
    keywords=[
        'aminoapps',
        'amino.fix',
        'amino.fix.fix',
        'amino',
        'amino-bot',
        'narvii',
        'api',
        'python',
        'python3',
        'python3.x',
        'minori',
        'imperialwool',
    ],
    python_requires='>=3.7',
)
