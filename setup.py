#!/usr/bin/env python3
"""
LocalAgentWeaverのセットアップスクリプト
"""

from setuptools import setup, find_packages
from pathlib import Path

# README内容を取得
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# requirements.txtから依存関係を取得
requirements = []
if (this_directory / "requirements.txt").exists():
    requirements = (this_directory / "requirements.txt").read_text(encoding='utf-8').splitlines()
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="localagentweaver",
    version="0.1.0",
    author="LocalAgentWeaver Team",
    author_email="",
    description="ローカル環境で動作するナレッジベース拡張型AIチャットアプリ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/LocalAgentWeaver",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/LocalAgentWeaver/issues",
        "Documentation": "https://github.com/yourusername/LocalAgentWeaver/wiki",
        "Source Code": "https://github.com/yourusername/LocalAgentWeaver",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Communications :: Chat",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "localagentweaver=localagentweaver.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)