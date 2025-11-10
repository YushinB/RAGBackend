"# RAG Python Backend

A comprehensive Retrieval-Augmented Generation (RAG) backend system built with Python, designed for processing and querying multimodal documents using advanced embedding and LLM technologies.

## Features

- **Multimodal Document Processing**: Support for PDF, Word, Excel, PowerPoint, and image files
- **Advanced Text Chunking**: Configurable chunking strategies for optimal retrieval performance
- **Vector Database Storage**: LanceDB integration for efficient similarity search
- **Multiple LLM Support**: Compatible with OpenAI GPT, Anthropic Claude, and local models
- **RESTful API**: FastAPI-based web interface with comprehensive endpoints
- **Asynchronous Processing**: Celery-based background task processing
- **Comprehensive Configuration**: Environment-based configuration management
- **Production Ready**: Docker support, logging, monitoring, and error handling

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Redis (for Celery task queue)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd RAG-Python-Backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. Initialize the application:
```bash
python -m src.core.app
```

## Project Structure

```
RAG-Python-Backend/
├── src/                        # Main application source code
│   ├── api/                    # FastAPI application and routes
│   ├── core/                   # Core configuration and utilities
│   ├── database/               # Database operations and models
│   ├── embeddings/             # Embedding generation and management
│   ├── llm/                    # LLM integration and management
│   ├── models/                 # Data models and schemas
│   ├── processors/             # Document processing modules
│   ├── query/                  # Query processing and retrieval
│   └── utils/                  # Utility functions and helpers
├── tests/                      # Test suite
├── config/                     # Configuration files
├── data/                       # Data storage directory
├── logs/                       # Application logs
├── scripts/                    # Deployment and utility scripts
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Configuration

The application uses environment-based configuration. Key settings include:

- **Database**: LanceDB connection and storage paths
- **Embeddings**: Model selection and parameters
- **LLM**: API keys and model configurations
- **Storage**: File upload limits and paths
- **Processing**: Chunking strategies and parameters

See `.env.example` for all available configuration options.

## Development

### Code Quality

The project uses several tools for maintaining code quality:

```bash
# Format code
black src/ tests/

# Lint code
ruff src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run quality checks:

```bash
pre-commit install
```

## API Documentation

Once the application is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]"
