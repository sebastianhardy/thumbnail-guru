"""Thumbnail Guru — setup."""
from setuptools import setup, find_packages
from pathlib import Path

readme = Path(__file__).parent / "README.md"
long_description = readme.read_text() if readme.exists() else ""

setup(
    name="thumbnail-guru",
    version="0.1.0",
    description="The thumb-stopper engine. Scored hooks + AI-generated scenes + brand-grade typography.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sebastian Hardy",
    author_email="",
    url="https://github.com/sebastianhardy/thumbnail-guru",
    license="Personal Use License (see LICENSE)",
    python_requires=">=3.10",
    packages=find_packages(exclude=("examples", "docs", "tests")),
    include_package_data=True,
    package_data={"tg": ["../data/*.yaml"]},
    install_requires=[
        "click>=8.1.0",
        "google-genai>=0.2.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "tg = tg.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Topic :: Multimedia :: Graphics",
    ],
)
