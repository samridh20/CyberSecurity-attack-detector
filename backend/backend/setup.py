"""
NIDS Backend Setup
Real-Time Network Intrusion Detection System Backend
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "docs" / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="nids-backend",
    version="1.0.0",
    description="Real-Time Network Intrusion Detection System Backend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="NIDS Team",
    author_email="team@nids.local",
    url="https://github.com/your-org/nids-backend",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "api": [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "websockets>=11.0.0",
        ],
        "performance": [
            "numba>=0.58.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "nids-backend=main:main",
            "nids-api=api.server:start_api_server",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    
    python_requires=">=3.8",
    
    keywords="network security intrusion detection nids cybersecurity",
    
    project_urls={
        "Bug Reports": "https://github.com/your-org/nids-backend/issues",
        "Source": "https://github.com/your-org/nids-backend",
        "Documentation": "https://nids-backend.readthedocs.io/",
    },
)