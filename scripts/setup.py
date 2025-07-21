#!/usr/bin/env python3
"""
Setup script for DDSM115 Motor Control GUI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ddsm115-motor-control",
    version="1.0.0",
    author="Motor Control Team",
    description="GUI application for controlling DDSM115 servo motors via RS485",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ddsm115-motor-control",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Engineering",
        "Topic :: Scientific/Engineering :: Electronic Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ddsm115-gui=ddsm115_gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "docs/*"],
    },
)