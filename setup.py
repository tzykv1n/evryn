# pip install -e .

from setuptools import setup, find_packages

setup(
    name="evryn",
    version="1.0.0",
    description="EVRYN : Unified Scientific Knowledge Discovery Platform",
    author="EVRYN Team",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "evryn=evryn.cli:main",
        ],
    },
)
