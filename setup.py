#!/usr/bin/env python
"""
Bangladesh Education Data API - Setup Configuration
"""

import os
import re
from setuptools import setup, find_packages

# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the version from the package
with open("src/__init__.py", "r", encoding="utf-8") as f:
    version = re.search(r'^__version__ = ["\']([^"\']+)["\']', f.read(), re.MULTILINE).group(1)

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Development requirements
with open("requirements-dev.txt", "r", encoding="utf-8") as f:
    dev_requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="bangladesh-education-data",
    version=version,
    author="BdREN Data Analytics Team",
    author_email="team@bdren.edu.bd",
    description="A comprehensive data analysis system for educational data in Bangladesh",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bangladesh-education-data",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    entry_points={
        "console_scripts": [
            "bangladesh-education=src.main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/bangladesh-education-data/issues",
        "Source": "https://github.com/yourusername/bangladesh-education-data",
    },
)
