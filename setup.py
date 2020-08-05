"""The python wrapper for IQ Option API package setup."""
from setuptools import (setup, find_packages)


setup(
    name="iqoptionapi",
    version="6.8.9.1",
    packages=find_packages(),
    install_requires=["pylint","requests","websocket-client==0.56"],
    include_package_data = True,
    description="IQ Option bot to run files with signals",
    long_description="Best IQ Option API for python",
    url="https://github.com/SandimL/Trader-BOT",
    author="Lu-Yi-Hsun",
    author_email="yihsun1992@gmail.com",
    zip_safe=False
)
