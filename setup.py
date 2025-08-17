"""
Setup script for Meta Ads Discord Bot
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="meta-ads-discord-bot",
    version="1.1.0",
    author="Your Name",
    description="A Discord bot for Meta Ads using LangGraph - Fixed API updates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/meta-ads-bot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "meta-ads-bot=main:main",
        ],
    },
)