from setuptools import setup, find_packages

setup(
    name="chat-miner",
    description="chat-miner provides lean parsers for every major platform transforming chats into pandas dataframes. Artistic visualizations allow you to explore your data and create artwork from your chats.",
    packages=find_packages(),
    install_requires=[
        "argparse",  # argparse is part of the Python standard library, so it's not in requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "chatminer = chatminer.cli:main",
        ],
    },
)
