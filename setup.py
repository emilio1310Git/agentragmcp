from setuptools import setup, find_packages

setup(
    name="agentragmcp",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "oracledb",
        "pydantic>=2.0",
        "geojson-pydantic",
        "uvicorn"
        # otras dependencias
    ],
    extras_require={
        "dev_and_test": ["pytest", "httpx", "pytest-cov", "pytest-mock"],
        # "dev": ["pytest", "httpx"],
        # "test": ["pytest-cov", "pytest-mock"]
    },
)