from setuptools import setup, find_packages

setup(
    name="agentragmcp",
    version="1.0.0",
    description="Asistente IA especializado en plantas con múltiples RAGs y sistema de agentes",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Tu Nombre",
    author_email="tu.email@ejemplo.com",
    url="https://github.com/tu-usuario/agentragmcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.7.4",
        "pydantic-settings>=2.4.0",
        
        # LangChain ecosystem
        "langchain>=0.2.16",
        "langchain-core>=0.2.38", 
        "langchain-community>=0.2.16",
        "langchain-chroma>=0.1.2",
        "langchain-ollama>=0.1.3",
        
        # Vector database
        "chromadb>=0.4.18",
        
        # LLM providers
        "ollama>=0.3.3",
        
        # HTTP and async
        "httpx>=0.27.0",
        "aiofiles>=23.2.1",
        
        # Configuration and utilities
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "python-multipart>=0.0.6",
        
        # Monitoring and logging
        "structlog>=23.2.0",
        "python-json-logger>=2.0.7",
    ],
    extras_require={
        "dev": [
            # Testing
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-httpx>=0.26.0",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            
            # Development tools
            "black>=23.12.0",
            "isort>=5.13.2",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            
            # Documentation
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
        "security": [
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
        ],
        "metrics": [
            "prometheus-client>=0.19.0",
        ],
        "mcp": [
            # MCP dependencies (cuando estén disponibles)
            # "mcp>=1.0.0",
        ],
        "database": [
            # Para historial persistente
            "sqlalchemy>=2.0.23",
            "alembic>=1.13.0",
            "asyncpg>=0.29.0",  # PostgreSQL
            "redis>=5.0.1",      # Para cache
            "aioredis>=2.0.1",
        ],
        "production": [
            "gunicorn>=21.2.0",
            "prometheus-client>=0.19.0",
            "redis>=5.0.1",
        ],
        "all": [
            # Incluye todas las dependencias opcionales
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1", 
            "pytest-httpx>=0.26.0",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "isort>=5.13.2",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "prometheus-client>=0.19.0",
            "sqlalchemy>=2.0.23",
            "redis>=5.0.1",
            "gunicorn>=21.2.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "agentragmcp=agentragmcp.api.app.main:main",
            "agentragmcp-init=scripts.init_agentragmcp:main",
        ],
    },
    include_package_data=True,
    package_data={
        "agentragmcp": [
            "data/configs/*.yaml",
            "api/static/*",
            "*.md",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/tu-usuario/agentragmcp/issues",
        "Source": "https://github.com/tu-usuario/agentragmcp",
        "Documentation": "https://agentragmcp.readthedocs.io/",
    },
    keywords=[
        "ai", "llm", "rag", "agents", "plants", "botany", 
        "fastapi", "langchain", "ollama", "chatbot",
        "agriculture", "pathology", "multi-agent"
    ],
)