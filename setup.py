from setuptools import setup, find_packages
LIBRARY_VERSION = "1.0.7b4"

# REQUIREMENTS

requirements = [
    "httpx>=0.27.0",
    "httpx[http2]",
    "httpx[socks]",
    "websocket-client>=1.3.1",
    "python-socks", 
    "setuptools"
]

requests_requirements = [
    "requests>=2.30.0",
    "requests[socks]"
]
aiohttp_requirements = [
    "aiohttp>=3.9.0",
    "aiohttp[speedups]",
    "aiohttp_socks"
]

# keywords

keywords = [
    'aminoapps',
    'amino.fix',
    'amino.fix.fix',
    'amino',
    'amino-bot',
    'narvii',
    'medialab',
    'api',
    'python',
    'python3',
    'python3.x',
    'minori',
    'imperialwool',
]

# setup

setup(
    license="MIT",

    name="amino.fix.fix",
    description="Library for Aminoapps",
    
    version=LIBRARY_VERSION,
    url="https://github.com/imperialwool/Amino.fix.fix",

    long_description_content_type="text/markdown",
    long_description=open("README.md", encoding="utf-8").read(),

    author="imperialwool",
    author_email="hi@iwool.dev",
    
    python_requires='>=3.8',
    packages=find_packages(),

    keywords=keywords,
    install_requires=requirements,
    extras_require={
        "requests": requests_requirements,
        "aiohttp": aiohttp_requirements,
    },
)
