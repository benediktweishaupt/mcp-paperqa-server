"""
Academic MCP Server - PDF Processing Engine Setup
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="academic-pdf-processing",
    version="0.1.0",
    description="Academic PDF processing engine for research document analysis",
    long_description=open("README.md", "r", encoding="utf-8").read() if open("README.md").readable() else "",
    long_description_content_type="text/markdown",
    author="Academic MCP Server Team",
    author_email="contact@academic-mcp.com",
    url="https://github.com/academic-mcp/server",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="academic research pdf processing mcp server",
    project_urls={
        "Bug Reports": "https://github.com/academic-mcp/server/issues",
        "Source": "https://github.com/academic-mcp/server",
        "Documentation": "https://academic-mcp.readthedocs.io/",
    },
)