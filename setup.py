from setuptools import find_packages, setup

setup(
    name="chat-miner",
    description="chat-miner provides lean parsers for every major platform transforming chats into pandas dataframes.\
         Artistic visualizations allow you to explore your data and create artwork from your chats.",
    packages=find_packages(),
    install_requires=[
        "argparse",
    ],
    entry_points={
        "console_scripts": [
            "chatminer = chatminer.cli:main",
        ],
    },
)
