from setuptools import setup, find_packages
LIBRARY_VERSION = "1.0.5b4"

requirements = [
    "httpx>=0.27.0",
    "httpx[http2]",
    "httpx[socks]",
    "websocket-client>=1.3.1", #not sure why it NEEDS 1.3.1 version, latest version works fine
    "python-socks", 
    "setuptools"
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
    version=LIBRARY_VERSION,
    author_email="hi@iwool.dev",
    description="Library for Aminoapps",
    url="https://github.com/imperialwool/Amino.fix.fix",
    packages=find_packages(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=requirements,
    keywords=keywords,
    python_requires='>=3.9',
)
