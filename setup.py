#!/usr/bin/env python
from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="UltimateBotWConverter",
    version="1.4.0a0",
    author="Nitram",
    description="A script to convert WiiU BotW mods to Switch",
    long_description=Path("README.md").read_text(),
    url="https://github.com/Nitr4m12/UltimateBotWConverter",
    python_requires=">=3.7<3.9",
    install_requires=Path("requirements.txt").read_text().splitlines(),
    include_package_data=True,
    packages=find_packages(),
    license='GNU General Public License v3.0',
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent"
    ],
    entry_points={
        "console_scripts": [
            "convert_to_switch = ubotw_converter.converter:main",
        ],
    },

)