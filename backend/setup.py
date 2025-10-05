"""
Setup script for the Real-Time Network Intrusion Detection System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="nids-realtime",
    version="1.0.0",
    description="Real-Time Network Intrusion Detection System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="NIDS Team",
    author_email="nids@example.com",
    url="https://github.com/example/nids-realtime",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=1.0.0',
        ],
        'plotting': [
            'matplotlib>=3.5.0',
            'seaborn>=0.11.0',
        ],
        'performance': [
            'numba>=0.58.0',
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
    ],
    entry_points={
        'console_scripts': [
            'nids=main:main',
            'nids-demo=scripts.demo:main',
            'nids-evaluate=scripts.evaluate_offline:main',
            'nids-export=scripts.export_matlab_metadata:main',
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/example/nids-realtime/issues",
        "Source": "https://github.com/example/nids-realtime",
        "Documentation": "https://github.com/example/nids-realtime/wiki",
    },
)