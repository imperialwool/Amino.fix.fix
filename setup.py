from setuptools import setup, find_packages

requirements = [
    "httpx",
    "httpx[http2]",
    "httpx[socks]",
    "websocket-client==1.3.1", 
    "setuptools", 
    "json_minify"
]

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

setup(
    name="amino.fix.fix",
    license="MIT",
    author="imperialwool",
    version="1.0.1",
    author_email="hi@iwool.dev",
    description="Library for Aminoapps",
    url="https://github.com/imperialwool/Amino.fix.fix",
    packages=find_packages(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=requirements,
    keywords=keywords,
    python_requires='>=3.7',
)
