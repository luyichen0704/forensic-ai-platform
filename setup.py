from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="forensic-ai-platform",
    version="0.1.0",
    author="luyichen0704",
    author_email="your-email@example.com",
    description="基于大模型的自动化取证平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luyichen0704/forensic-ai-platform",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "gpu": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "forensic-ai=core.cli:main",
        ],
    },
)
