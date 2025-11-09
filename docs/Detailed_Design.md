# Detailed Design Document

## Document Information

- **Project Name**: RAG (Retrieval-Augmented Generation) Python Backend
- **Document Version**: 1.0
- **Date**: November 9, 2025
- **Standard**: ISO/IEC/IEEE 26514

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Design](#4-data-design)
5. [Interface Design](#5-interface-design)
6. [Implementation Requirements](#6-implementation-requirements)
7. [Security Considerations](#7-security-considerations)
8. [Performance Requirements](#8-performance-requirements)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Architecture](#10-deployment-architecture)

## 1. Introduction

### 1.1 Purpose

This detailed design document provides comprehensive technical specifications for the RAG Python Backend system. It describes the architecture, component design, data structures, interfaces, and implementation requirements necessary for developing a production-ready system.

### 1.2 Scope

The document covers the complete backend system including:

- Data ingestion and processing pipeline
- Embedding generation and storage
- Vector database operations
- Query processing and retrieval
- LLM integration and response generation
- API interfaces for frontend integration

### 1.3 Intended Audience

- Software developers implementing the system
- System architects reviewing the design
- Quality assurance engineers developing test plans
- DevOps engineers planning deployment
- Project managers overseeing development

### 1.4 Document Conventions

- **Bold text**: Important terms and concepts
- *Italic text*: File names, variable names, and references
- `Code blocks`: Code snippets, commands, and technical values
- [Links]: References to other sections or external resources

### 1.5 References

- ISO/IEC/IEEE 26514:2022 - Systems and software engineering
- LanceDB Documentation
- BGE Models Documentation
- Qodo-Embed-1 Model Documentation
- Python 3.11+ Documentation
- Rust FFI Documentation

## 2. System Architecture

### 2.1 Architectural Overview

The RAG Python Backend follows a modular, pipeline-based architecture with the following key characteristics:

- **Layered Architecture**: Separation of concerns across distinct layers
- **Microservices-Ready**: Components designed for potential service isolation
- **Event-Driven**: Asynchronous processing for scalability
- **Plugin Architecture**: Extensible design for adding new data processors and models

### 2.2 High-Level Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│                      (Chatbot Interface)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────┴────────────────────────────────────┐
│                       API Gateway Layer                          │
│                  (FastAPI/Flask Backend)                         │
└─────┬────────────────┬────────────────┬────────────────┬────────┘
      │                │                │                │
      ▼                ▼                ▼                ▼
┌──────────┐   ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│  Data    │   │  Embedding   │  │    Query     │  │   LLM    │
│Processing│   │   Module     │  │  Processing  │  │Integration│
│  Module  │   │              │  │   Module     │  │  Module  │
└────┬─────┘   └──────┬───────┘  └──────┬───────┘  └─────┬────┘
     │                │                  │                 │
     │                ▼                  │                 │
     │         ┌─────────────┐           │                 │
     └────────►│  LanceDB    │◄──────────┘                 │
               │   Vector    │                             │
               │  Database   │                             │
               └─────────────┘                             │
                                                           │
               ┌─────────────────────────────────────────┐ │
               │      LLM Service (Rust Library)         │◄┘
               │         (API Communication)             │
               └─────────────────────────────────────────┘
```

### 2.3 Component Interaction Flow

#### 2.3.1 Data Ingestion Flow

1. User uploads document through API
2. Data Processing Module identifies file type
3. Appropriate processor extracts and chunks content
4. Embedding Module generates vector representations
5. Vectors stored in LanceDB with metadata

#### 2.3.2 Query Processing Flow

1. User submits query through API
2. Query Processing Module generates query embedding
3. LanceDB performs similarity search
4. Relevant context retrieved and ranked
5. Context combined with query to create prompt
6. LLM generates response via Rust integration
7. Response returned to frontend

### 2.4 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI | High-performance async API |
| Data Processing | Python 3.11+ | Core processing logic |
| Vector Database | LanceDB | Embedding storage and retrieval |
| Embedding Models | BGE/Qodo-Embed-1 | Text-to-vector conversion |
| LLM Integration | Rust (PyO3) | High-performance LLM interface |
| Task Queue | Celery + Redis | Async job processing |
| Caching | Redis | Query result caching |
| Configuration | Pydantic | Type-safe configuration |

## 3. Component Design

### 3.1 Data Processing Module

#### 3.1.1 Purpose

The Data Processing Module is responsible for ingesting various file formats, extracting text content, and preparing it for embedding generation through intelligent chunking strategies.

#### 3.1.2 Class Diagram

```python
# Core Classes and Interfaces

class DataProcessor(ABC):
    """Abstract base class for all data processors"""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Check if processor can handle the file type"""
        pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from file"""
        pass
    
    @abstractmethod
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[TextChunk]:
        """Split text into chunks with overlap"""
        pass

class TextChunk:
    """Represents a chunk of processed text"""
    content: str
    metadata: Dict[str, Any]
    source_file: str
    chunk_index: int
    start_position: int
    end_position: int
    
class PDFProcessor(DataProcessor):
    """Processor for PDF documents"""
    pass

class WordProcessor(DataProcessor):
    """Processor for Word documents (.docx)"""
    pass

class MarkdownProcessor(DataProcessor):
    """Processor for Markdown files"""
    pass

class ExcelProcessor(DataProcessor):
    """Processor for Excel spreadsheets"""
    pass

class TextFileProcessor(DataProcessor):
    """Processor for plain text files"""
    pass

class ProcessorFactory:
    """Factory for creating appropriate processor"""
    
    @staticmethod
    def get_processor(file_path: str) -> DataProcessor:
        """Return appropriate processor for file type"""
        pass
```

#### 3.1.3 Key Algorithms

**Chunking Strategy**:

1. **Semantic Chunking**: Preserve paragraph and sentence boundaries
2. **Fixed-Size Chunking**: Fallback for unstructured text
3. **Overlap Strategy**: Include context from adjacent chunks

**Algorithm Parameters**:

```python
class ChunkingConfig:
    chunk_size: int = 512  # tokens
    overlap_size: int = 128  # tokens
    min_chunk_size: int = 100  # tokens
    max_chunk_size: int = 1024  # tokens
    respect_sentence_boundaries: bool = True
    respect_paragraph_boundaries: bool = True
```

#### 3.1.4 Data Flow

```text
Input File → File Type Detection → Processor Selection → 
Text Extraction → Chunking → Metadata Enrichment → Output Chunks
```

#### 3.1.5 Error Handling

- **File Not Found**: Return error with file path
- **Unsupported Format**: Suggest supported formats
- **Corrupted File**: Log error and skip processing
- **Extraction Failure**: Retry with alternative method
- **Memory Overflow**: Process file in streaming mode

### 3.2 Embedding Module

#### 3.2.1 Purpose

Convert text chunks into dense vector representations using pre-trained embedding models for semantic similarity search.

#### 3.2.2 Class Diagram

```python
class EmbeddingModel(ABC):
    """Abstract base for embedding models"""
    
    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text batch"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Return embedding dimension"""
        pass

class BGEEmbedding(EmbeddingModel):
    """BGE model implementation"""
    model_name: str = "BAAI/bge-base-en-v1.5"
    dimension: int = 768
    batch_size: int = 32
    
    def __init__(self):
        self.model = SentenceTransformer(self.model_name)
    
    def encode(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, batch_size=self.batch_size)

class QodoEmbedding(EmbeddingModel):
    """Qodo-Embed-1 implementation"""
    model_name: str = "Qodo/qodo-embed-1"
    dimension: int = 1024
    batch_size: int = 16

class EmbeddingService:
    """Service for managing embedding generation"""
    
    def __init__(self, model: EmbeddingModel):
        self.model = model
        self.cache = EmbeddingCache()
    
    async def embed_chunks(self, chunks: List[TextChunk]) -> List[EmbeddedChunk]:
        """Generate embeddings for text chunks"""
        pass
    
    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts in batches for efficiency"""
        pass

class EmbeddedChunk:
    """Text chunk with embedding"""
    chunk: TextChunk
    embedding: np.ndarray
    model_name: str
    timestamp: datetime
```

#### 3.2.3 Embedding Process

1. **Input**: List of TextChunk objects
2. **Preprocessing**: Normalize text, handle special characters
3. **Batching**: Group chunks for efficient processing
4. **Encoding**: Generate embeddings using model
5. **Validation**: Ensure correct dimensions and types
6. **Output**: List of EmbeddedChunk objects

#### 3.2.4 Performance Optimization

- **Batch Processing**: Process multiple chunks simultaneously
- **GPU Acceleration**: Utilize CUDA if available
- **Caching**: Store embeddings for repeated text
- **Async Processing**: Non-blocking embedding generation
- **Model Quantization**: Use int8 quantization for faster inference

### 3.3 Vector Database Module

#### 3.3.1 Purpose

Store and retrieve embeddings efficiently using LanceDB for similarity search operations.

#### 3.3.2 Class Diagram

```python
class VectorDatabase:
    """LanceDB wrapper for vector operations"""
    
    def __init__(self, db_path: str, table_name: str):
        self.db = lancedb.connect(db_path)
        self.table_name = table_name
    
    async def insert_embeddings(self, chunks: List[EmbeddedChunk]) -> bool:
        """Insert embeddings into database"""
        pass
    
    async def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[SearchResult]:
        """Perform similarity search"""
        pass
    
    async def delete_by_source(self, source_file: str) -> int:
        """Delete all chunks from a source file"""
        pass
    
    async def update_metadata(self, chunk_id: str, metadata: Dict) -> bool:
        """Update chunk metadata"""
        pass

class SearchResult:
    """Result from similarity search"""
    chunk: TextChunk
    score: float
    distance: float
    metadata: Dict[str, Any]

class VectorSchema:
    """Schema for vector database"""
    id: str  # Unique identifier
    content: str  # Original text
    embedding: np.ndarray  # Vector representation
    source_file: str  # Source document
    chunk_index: int  # Position in document
    metadata: Dict[str, Any]  # Additional information
    created_at: datetime
    updated_at: datetime
```

#### 3.3.3 Indexing Strategy

- **Index Type**: IVF-PQ (Inverted File with Product Quantization)
- **Distance Metric**: Cosine similarity
- **Partitions**: Automatically determined based on dataset size
- **Replication**: Configurable for high availability

#### 3.3.4 Query Optimization

```python
class QueryOptimizer:
    """Optimize vector search queries"""
    
    def optimize_top_k(self, query: str, context_length: int) -> int:
        """Calculate optimal top_k based on context"""
        pass
    
    def rerank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Re-rank results using cross-encoder"""
        pass
    
    def filter_by_metadata(self, results: List[SearchResult], filters: Dict) -> List[SearchResult]:
        """Apply metadata filters"""
        pass
```

### 3.4 Query Processing Module

#### 3.4.1 Purpose

Process user queries, retrieve relevant context, and construct prompts for LLM generation.

#### 3.4.2 Class Diagram

```python
class QueryProcessor:
    """Main query processing orchestrator"""
    
    def __init__(self, embedding_service: EmbeddingService, 
                 vector_db: VectorDatabase,
                 llm_client: LLMClient):
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder()
    
    async def process_query(self, query: str, config: QueryConfig) -> QueryResult:
        """Process complete query pipeline"""
        pass
    
    async def retrieve_context(self, query_embedding: np.ndarray, top_k: int) -> List[TextChunk]:
        """Retrieve relevant context from vector DB"""
        pass

class PromptBuilder:
    """Construct prompts for LLM"""
    
    def build_prompt(self, query: str, context: List[TextChunk], 
                    system_prompt: str = None) -> str:
        """Build complete prompt with context"""
        pass
    
    def format_context(self, chunks: List[TextChunk]) -> str:
        """Format retrieved chunks for context"""
        pass

class QueryConfig:
    """Configuration for query processing"""
    top_k: int = 5
    temperature: float = 0.7
    max_tokens: int = 1024
    include_sources: bool = True
    rerank: bool = True
    
class QueryResult:
    """Complete query result"""
    query: str
    response: str
    sources: List[TextChunk]
    metadata: Dict[str, Any]
    processing_time: float
```

#### 3.4.3 Prompt Template

```python
PROMPT_TEMPLATE = """
You are a helpful AI assistant. Use the following context to answer the user's question.
If you cannot answer based on the context, say so clearly.

Context:
{context}

Question: {query}

Answer:
"""
```

#### 3.4.4 Context Ranking

1. **Initial Retrieval**: Get top-k candidates using vector similarity
2. **Re-ranking**: Use cross-encoder for fine-grained relevance
3. **Diversity**: Ensure context diversity to avoid redundancy
4. **Recency**: Optionally weight recent documents higher

### 3.5 LLM Integration Module

#### 3.5.1 Purpose

Interface with LLM models through Rust library for efficient response generation.

#### 3.5.2 Class Diagram

```python
class LLMClient:
    """Python interface to Rust LLM library"""
    
    def __init__(self, config: LLMConfig):
        self.rust_client = initialize_rust_llm(config)
        self.request_queue = RequestQueue()
    
    async def generate(self, prompt: str, config: GenerationConfig) -> LLMResponse:
        """Generate response from prompt"""
        pass
    
    async def generate_stream(self, prompt: str, config: GenerationConfig) -> AsyncIterator[str]:
        """Generate response with streaming"""
        pass
    
    def validate_prompt(self, prompt: str) -> bool:
        """Validate prompt before generation"""
        pass

class LLMConfig:
    """Configuration for LLM"""
    model_name: str
    api_endpoint: str
    api_key: str
    timeout: int = 30
    retry_count: int = 3
    
class GenerationConfig:
    """Parameters for text generation"""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    stop_sequences: List[str] = []
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

class LLMResponse:
    """Response from LLM"""
    text: str
    finish_reason: str
    tokens_used: int
    latency: float
    metadata: Dict[str, Any]
```

#### 3.5.3 Rust FFI Interface

##### Rust Implementation Example

The following shows a conceptual implementation of the Rust LLM client using PyO3 for Python integration:

```python
# Python-like pseudocode representing Rust FFI interface

class RustLLMClient:
    """Rust LLM client exposed to Python via PyO3"""
    
    def __init__(self, config: ClientConfig):
        """Initialize LLM client"""
        pass
    
    def generate(self, prompt: str, config: GenerationConfig) -> str:
        """Generate response synchronously"""
        pass
    
    def generate_stream(self, prompt: str, config: GenerationConfig) -> Iterator[str]:
        """Generate response with streaming"""
        pass
```

**Note**: The actual implementation is written in Rust and compiled as a Python extension module using PyO3/Maturin.

#### 3.5.4 Error Handling

- **Timeout**: Retry with exponential backoff
- **Rate Limiting**: Implement token bucket algorithm
- **Connection Error**: Fallback to alternative endpoint
- **Invalid Response**: Log and return error message
- **Context Length Exceeded**: Truncate or summarize context

## 4. Data Design

### 4.1 Data Models

#### 4.1.1 Document Model

```python
class Document(BaseModel):
    """Represents an uploaded document"""
    id: UUID = Field(default_factory=uuid4)
    filename: str
    file_path: str
    file_type: str
    file_size: int  # bytes
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus
    chunk_count: int = 0
    metadata: Dict[str, Any] = {}
    
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

#### 4.1.2 Chunk Model

```python
class Chunk(BaseModel):
    """Represents a text chunk"""
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    chunk_index: int
    start_position: int
    end_position: int
    embedding_vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 4.1.3 Query Model

```python
class Query(BaseModel):
    """Represents a user query"""
    id: UUID = Field(default_factory=uuid4)
    query_text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    response: Optional[str] = None
    sources: List[UUID] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None
```

### 4.2 Database Schema

#### 4.2.1 Relational Database (PostgreSQL)

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Queries table (for analytics)
CREATE TABLE queries (
    id UUID PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    response TEXT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query-Source mapping
CREATE TABLE query_sources (
    query_id UUID REFERENCES queries(id),
    chunk_id UUID,
    relevance_score FLOAT,
    PRIMARY KEY (query_id, chunk_id)
);

-- Create indexes
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_upload_date ON documents(upload_date);
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_queries_user_id ON queries(user_id);
```

#### 4.2.2 Vector Database Schema (LanceDB)

```python
# LanceDB table schema
vector_table_schema = pa.schema([
    pa.field("id", pa.string()),
    pa.field("document_id", pa.string()),
    pa.field("content", pa.string()),
    pa.field("embedding", pa.list_(pa.float32(), 768)),  # Dimension depends on model
    pa.field("chunk_index", pa.int32()),
    pa.field("start_position", pa.int32()),
    pa.field("end_position", pa.int32()),
    pa.field("source_file", pa.string()),
    pa.field("metadata", pa.string()),  # JSON string
    pa.field("created_at", pa.timestamp('ms')),
])
```

### 4.3 Data Storage Strategy

#### 4.3.1 File Storage

- **Uploaded Files**: Store in filesystem or S3-compatible storage
- **Directory Structure**:

  ```text
  /data
    /uploads
      /{user_id}
        /{document_id}
          /original
          /processed
    /embeddings
      /cache
    /models
      /bge
      /qodo
  ```

#### 4.3.2 Caching Strategy

```python
class CacheManager:
    """Manage caching for frequently accessed data"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl_embeddings = 3600  # 1 hour
        self.ttl_queries = 1800  # 30 minutes
    
    async def cache_embedding(self, text: str, embedding: np.ndarray):
        """Cache embedding for text"""
        key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"
        await self.redis.setex(key, self.ttl_embeddings, embedding.tobytes())
    
    async def get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Retrieve cached embedding"""
        key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"
        data = await self.redis.get(key)
        return np.frombuffer(data) if data else None
```

## 5. Interface Design

### 5.1 REST API Endpoints

#### 5.1.1 Document Management

```python
# Upload document
POST /api/v1/documents
Content-Type: multipart/form-data
Body: {
    "file": <file>,
    "metadata": {
        "tags": ["tag1", "tag2"],
        "description": "Document description"
    }
}
Response: {
    "document_id": "uuid",
    "status": "processing",
    "message": "Document uploaded successfully"
}

# Get document status
GET /api/v1/documents/{document_id}
Response: {
    "document_id": "uuid",
    "filename": "example.pdf",
    "status": "completed",
    "chunk_count": 42,
    "created_at": "2025-11-09T10:00:00Z"
}

# List documents
GET /api/v1/documents?page=1&limit=20
Response: {
    "documents": [...],
    "total": 100,
    "page": 1,
    "pages": 5
}

# Delete document
DELETE /api/v1/documents/{document_id}
Response: {
    "message": "Document deleted successfully"
}
```

#### 5.1.2 Query Operations

```python
# Submit query
POST /api/v1/query
Content-Type: application/json
Body: {
    "query": "What is the main topic?",
    "top_k": 5,
    "temperature": 0.7,
    "include_sources": true
}
Response: {
    "query_id": "uuid",
    "response": "The main topic is...",
    "sources": [
        {
            "document_id": "uuid",
            "content": "...",
            "score": 0.95
        }
    ],
    "processing_time": 1.23
}

# Stream query response
POST /api/v1/query/stream
Content-Type: application/json
Body: {
    "query": "Explain this topic in detail",
    "config": {...}
}
Response: Server-Sent Events stream
```

#### 5.1.3 System Operations

```python
# Health check
GET /api/v1/health
Response: {
    "status": "healthy",
    "version": "1.0.0",
    "components": {
        "database": "connected",
        "vector_db": "connected",
        "llm_service": "available"
    }
}

# Get statistics
GET /api/v1/stats
Response: {
    "total_documents": 150,
    "total_chunks": 5420,
    "total_queries": 1234,
    "avg_response_time": 1.45
}
```

### 5.2 WebSocket Interface

```python
# Real-time query processing
WS /api/v1/ws/query

# Client -> Server
{
    "action": "query",
    "data": {
        "query": "User question",
        "session_id": "session-uuid"
    }
}

# Server -> Client (streaming response)
{
    "type": "chunk",
    "data": "Partial response..."
}

{
    "type": "complete",
    "data": {
        "full_response": "Complete response",
        "sources": [...]
    }
}
```

### 5.3 Internal Module Interfaces

#### 5.3.1 Processor Interface

```python
class IDataProcessor(Protocol):
    """Interface for data processors"""
    
    def can_process(self, file_path: str) -> bool:
        """Check if processor can handle file"""
        ...
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from file"""
        ...
    
    def chunk_text(self, text: str, config: ChunkingConfig) -> List[TextChunk]:
        """Chunk text according to configuration"""
        ...
```

#### 5.3.2 Embedding Interface

```python
class IEmbeddingModel(Protocol):
    """Interface for embedding models"""
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings"""
        ...
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        ...
    
    def batch_size(self) -> int:
        """Get optimal batch size"""
        ...
```

## 6. Implementation Requirements

### 6.1 Development Environment

#### 6.1.1 Required Software

- Python 3.11 or higher
- Rust 1.70+ (for LLM integration)
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Git

#### 6.1.2 Python Dependencies

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Data Processing
pypdf2==3.0.1
python-docx==1.1.0
openpyxl==3.1.2
markdown==3.5.1
beautifulsoup4==4.12.2

# Machine Learning
sentence-transformers==2.2.2
transformers==4.35.0
torch==2.1.0
numpy==1.24.3

# Vector Database
lancedb==0.3.0
pyarrow==14.0.0

# Async & Task Queue
celery==5.3.4
redis==5.0.1
aioredis==2.0.1

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1

# Utilities
python-multipart==0.0.6
python-dotenv==1.0.0
pyyaml==6.0.1
httpx==0.25.1

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
ruff==0.1.6
mypy==1.7.1
```

### 6.2 Configuration Management

#### 6.2.1 Configuration File Structure

```yaml
# config.yaml
app:
  name: "RAG Backend"
  version: "1.0.0"
  environment: "development"
  debug: true

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: true

database:
  postgres:
    host: "localhost"
    port: 5432
    database: "rag_db"
    user: "rag_user"
    password: "${POSTGRES_PASSWORD}"
  
  lancedb:
    path: "./data/lancedb"
    table_name: "embeddings"
  
  redis:
    host: "localhost"
    port: 6379
    db: 0

embedding:
  model: "bge"  # or "qodo"
  batch_size: 32
  dimension: 768
  device: "cuda"  # or "cpu"

chunking:
  chunk_size: 512
  overlap: 128
  min_size: 100
  max_size: 1024

llm:
  api_endpoint: "${LLM_API_ENDPOINT}"
  api_key: "${LLM_API_KEY}"
  model_name: "llama2-7b"
  timeout: 30
  max_tokens: 1024
  temperature: 0.7

storage:
  upload_dir: "./data/uploads"
  max_file_size: 52428800  # 50MB
  allowed_extensions:
    - "pdf"
    - "docx"
    - "txt"
    - "md"
    - "xlsx"

logging:
  level: "INFO"
  format: "json"
  output: "stdout"
  file: "./logs/app.log"
```

#### 6.2.2 Environment Variables

```bash
# .env
ENVIRONMENT=development
POSTGRES_PASSWORD=secure_password
LLM_API_ENDPOINT=http://localhost:8080
LLM_API_KEY=your_api_key_here
REDIS_PASSWORD=redis_password
SECRET_KEY=your_secret_key
```

### 6.3 Code Organization

```text
rag-backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   ├── queries.py
│   │   │   └── health.py
│   │   ├── dependencies.py
│   │   └── middleware.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── pdf_processor.py
│   │   ├── word_processor.py
│   │   ├── markdown_processor.py
│   │   └── excel_processor.py
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── bge_model.py
│   │   └── qodo_model.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   ├── vector_store.py
│   │   └── cache.py
│   ├── query/
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   ├── prompt_builder.py
│   │   └── reranker.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── rust_interface.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── chunk.py
│   │   └── query.py
│   └── utils/
│       ├── __init__.py
│       ├── text_utils.py
│       └── validation.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── rust_llm/
│   ├── src/
│   │   └── lib.rs
│   ├── Cargo.toml
│   └── pyproject.toml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── setup.sh
│   └── migrate.py
├── config/
│   ├── config.yaml
│   └── config.prod.yaml
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 6.4 Coding Standards

#### 6.4.1 Python Style Guide

- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 120 characters
- Use docstrings for all public methods
- Format code with Black
- Lint with Ruff
- Type check with MyPy

#### 6.4.2 Code Example

```python
from typing import List, Optional
from pydantic import BaseModel
import numpy as np


class TextChunk(BaseModel):
    """Represents a chunk of processed text.
    
    Attributes:
        content: The text content of the chunk
        metadata: Additional information about the chunk
        source_file: Path to the source document
        chunk_index: Position of chunk in the document
    """
    content: str
    metadata: dict[str, Any]
    source_file: str
    chunk_index: int
    
    class Config:
        """Pydantic configuration."""
        frozen = True


async def process_document(
    file_path: str,
    chunk_size: int = 512,
    overlap: int = 128,
) -> List[TextChunk]:
    """Process a document into text chunks.
    
    Args:
        file_path: Path to the document file
        chunk_size: Target size for each chunk in tokens
        overlap: Number of overlapping tokens between chunks
        
    Returns:
        List of TextChunk objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ProcessingError: If document processing fails
    """
    # Implementation here
    pass
```

## 7. Security Considerations

### 7.1 Authentication & Authorization

#### 7.1.1 API Authentication

```python
# JWT-based authentication
class AuthMiddleware:
    """Middleware for API authentication"""
    
    async def authenticate_request(self, request: Request) -> Optional[User]:
        """Validate JWT token and return user"""
        token = request.headers.get("Authorization")
        if not token:
            raise UnauthorizedException()
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            return await get_user(user_id)
        except JWTError:
            raise UnauthorizedException()
```

#### 7.1.2 Access Control

- **Role-Based Access Control (RBAC)**:
  - Admin: Full system access
  - User: Upload and query own documents
  - Guest: Read-only query access

### 7.2 Input Validation

```python
class DocumentUpload(BaseModel):
    """Validated document upload request"""
    
    file: UploadFile = Field(..., description="Document file")
    
    @validator('file')
    def validate_file(cls, v):
        """Validate file type and size"""
        allowed_types = {'application/pdf', 'text/plain', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        
        if v.content_type not in allowed_types:
            raise ValueError(f"File type {v.content_type} not allowed")
        
        if v.size > MAX_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE}")
        
        return v

class QueryRequest(BaseModel):
    """Validated query request"""
    
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize query text"""
        # Remove potentially harmful characters
        v = v.strip()
        v = re.sub(r'[^\w\s\?\.\,\-]', '', v)
        return v
```

### 7.3 Data Protection

#### 7.3.1 Encryption

- **Data at Rest**: Encrypt uploaded files using AES-256
- **Data in Transit**: Use TLS 1.3 for all API communications
- **Database**: Enable PostgreSQL encryption
- **Secrets**: Store API keys in secure vault (e.g., HashiCorp Vault)

#### 7.3.2 Privacy

- **PII Detection**: Scan documents for personally identifiable information
- **Data Retention**: Implement configurable retention policies
- **User Consent**: Track and honor user data preferences
- **Audit Logging**: Log all data access and modifications

### 7.4 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/query")
@limiter.limit("10/minute")
async def query(request: Request, query_req: QueryRequest):
    """Rate-limited query endpoint"""
    pass
```

## 8. Performance Requirements

### 8.1 Performance Targets

| Operation | Target Latency | Target Throughput |
|-----------|----------------|-------------------|
| Document Upload | < 5s for 10MB file | 100 uploads/hour |
| Text Extraction | < 2s per MB | - |
| Embedding Generation | < 1s per 1000 tokens | 10,000 tokens/sec |
| Vector Search | < 100ms | 1000 queries/sec |
| Query Processing | < 2s end-to-end | 500 queries/sec |
| LLM Response | < 5s | 200 queries/sec |

### 8.2 Optimization Strategies

#### 8.2.1 Caching

```python
class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.embedding_cache = LRUCache(maxsize=10000)
        self.query_cache = TTLCache(maxsize=1000, ttl=1800)
    
    @lru_cache(maxsize=1000)
    def get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Cache embeddings for frequently used texts"""
        pass
    
    async def cache_query_result(self, query_hash: str, result: QueryResult):
        """Cache query results for duplicate queries"""
        await self.redis.setex(
            f"query:{query_hash}",
            1800,  # 30 minutes
            pickle.dumps(result)
        )
```

#### 8.2.2 Batch Processing

```python
class BatchProcessor:
    """Process operations in batches for efficiency"""
    
    def __init__(self, batch_size: int = 32, max_wait: float = 0.1):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.queue = asyncio.Queue()
    
    async def process_batch(self, items: List[Any]) -> List[Any]:
        """Process items in batches"""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await self._process_single_batch(batch)
            results.extend(batch_results)
        return results
```

#### 8.2.3 Async Processing

- Use asyncio for I/O-bound operations
- Implement connection pooling for database
- Use task queues (Celery) for long-running jobs
- Enable GPU acceleration for embeddings

### 8.3 Scalability Design

#### 8.3.1 Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  api:
    image: rag-backend:latest
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 4G
  
  worker:
    image: rag-backend:latest
    command: celery -A tasks worker
    deploy:
      replicas: 8
```

#### 8.3.2 Load Balancing

- Use Nginx or Traefik for API load balancing
- Distribute embedding tasks across multiple workers
- Implement read replicas for PostgreSQL
- Use Redis cluster for caching

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/unit/test_processors.py
import pytest
from src.processors.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test PDF processing functionality"""
    
    @pytest.fixture
    def processor(self):
        return PDFProcessor()
    
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        # Create sample PDF for testing
        pdf_path = tmp_path / "test.pdf"
        # ... create PDF
        return str(pdf_path)
    
    def test_can_process_pdf(self, processor):
        """Test PDF file type detection"""
        assert processor.can_process("document.pdf")
        assert not processor.can_process("document.docx")
    
    def test_extract_text_from_pdf(self, processor, sample_pdf):
        """Test text extraction from PDF"""
        text = processor.extract_text(sample_pdf)
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_chunk_text(self, processor):
        """Test text chunking"""
        text = "This is a test document. " * 100
        chunks = processor.chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 0
        assert all(isinstance(c.content, str) for c in chunks)
        assert all(c.chunk_index >= 0 for c in chunks)
    
    def test_empty_pdf_handling(self, processor, tmp_path):
        """Test handling of empty PDF"""
        empty_pdf = tmp_path / "empty.pdf"
        # ... create empty PDF
        
        with pytest.raises(ValueError, match="Empty document"):
            processor.extract_text(str(empty_pdf))
```

### 9.2 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
from src.processors import ProcessorFactory
from src.embeddings import EmbeddingService
from src.database import VectorDatabase


@pytest.mark.integration
class TestEmbeddingPipeline:
    """Test complete embedding pipeline"""
    
    @pytest.fixture
    async def setup_pipeline(self):
        """Set up test pipeline components"""
        processor = ProcessorFactory.get_processor("test.pdf")
        embedding_service = EmbeddingService(model_name="bge")
        vector_db = VectorDatabase(db_path="./test_db", table_name="test")
        
        yield processor, embedding_service, vector_db
        
        # Cleanup
        await vector_db.close()
    
    @pytest.mark.asyncio
    async def test_complete_pipeline(self, setup_pipeline, sample_document):
        """Test document processing through complete pipeline"""
        processor, embedding_service, vector_db = setup_pipeline
        
        # Extract and chunk
        text = processor.extract_text(sample_document)
        chunks = processor.chunk_text(text)
        
        # Generate embeddings
        embedded_chunks = await embedding_service.embed_chunks(chunks)
        
        # Store in database
        success = await vector_db.insert_embeddings(embedded_chunks)
        assert success
        
        # Verify retrieval
        query_embedding = await embedding_service.encode("test query")
        results = await vector_db.search(query_embedding, top_k=5)
        assert len(results) > 0
```

### 9.3 End-to-End Tests

```python
# tests/e2e/test_api.py
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestAPIEndpoints:
    """End-to-end API tests"""
    
    @pytest.mark.asyncio
    async def test_document_upload_and_query(self, client: AsyncClient):
        """Test complete document upload and query flow"""
        
        # Upload document
        files = {"file": ("test.pdf", open("test.pdf", "rb"), "application/pdf")}
        response = await client.post("/api/v1/documents", files=files)
        assert response.status_code == 200
        
        document_id = response.json()["document_id"]
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Check status
        response = await client.get(f"/api/v1/documents/{document_id}")
        assert response.json()["status"] == "completed"
        
        # Submit query
        query_data = {
            "query": "What is the main topic?",
            "top_k": 5
        }
        response = await client.post("/api/v1/query", json=query_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
```

### 9.4 Performance Tests

```python
# tests/performance/test_load.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.performance
class TestPerformance:
    """Performance and load tests"""
    
    def test_concurrent_queries(self, client):
        """Test system under concurrent load"""
        
        queries = ["test query"] * 100
        
        def submit_query(query):
            start = time.time()
            response = client.post("/api/v1/query", json={"query": query})
            latency = time.time() - start
            return response.status_code == 200, latency
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(submit_query, queries))
        
        successes = sum(1 for success, _ in results if success)
        latencies = [lat for _, lat in results]
        
        assert successes / len(queries) > 0.95  # 95% success rate
        assert sum(latencies) / len(latencies) < 2.0  # Average < 2s
        assert max(latencies) < 5.0  # Max < 5s
    
    def test_embedding_throughput(self, embedding_service):
        """Test embedding generation throughput"""
        
        texts = ["test text " * 50] * 1000
        
        start = time.time()
        embeddings = embedding_service.batch_encode(texts)
        duration = time.time() - start
        
        throughput = len(texts) / duration
        assert throughput > 100  # > 100 texts/second
```

## 10. Deployment Architecture

### 10.1 Docker Configuration

#### 10.1.1 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for LLM integration)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY rust_llm/ ./rust_llm/

# Build Rust extension
RUN cd rust_llm && maturin build --release

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 10.1.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: rag_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=production
      - POSTGRES_HOST=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - LLM_API_ENDPOINT=${LLM_API_ENDPOINT}
      - LLM_API_KEY=${LLM_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A src.tasks worker --loglevel=info --concurrency=4
    environment:
      - ENVIRONMENT=production
      - POSTGRES_HOST=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 4

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### 10.2 Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-backend-api
  template:
    metadata:
      labels:
        app: rag-backend-api
    spec:
      containers:
      - name: api
        image: rag-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: password
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: rag-backend-service
spec:
  selector:
    app: rag-backend-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 10.3 Monitoring & Logging

#### 10.3.1 Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
active_queries = Gauge('active_queries', 'Number of active queries')
embedding_cache_hits = Counter('embedding_cache_hits_total', 'Cache hits')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_duration.observe(duration)
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    
    return response
```

#### 10.3.2 Logging Configuration

```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging"""
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        timestamp=True
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Usage
logger = setup_logging()
logger.info("Document processed", extra={
    "document_id": doc_id,
    "chunks": chunk_count,
    "duration": processing_time
})
```

### 10.4 CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=src tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Black
        run: black --check src/
      
      - name: Run Ruff
        run: ruff check src/
      
      - name: Run MyPy
        run: mypy src/

  build:
    needs: [test, lint]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t rag-backend:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push rag-backend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/rag-backend-api api=rag-backend:${{ github.sha }}
          kubectl rollout status deployment/rag-backend-api
```

## Appendices

### Appendix A: Glossary

- **RAG**: Retrieval-Augmented Generation
- **Embedding**: Dense vector representation of text
- **Vector Database**: Database optimized for similarity search
- **Chunking**: Process of splitting text into smaller pieces
- **LLM**: Large Language Model
- **Semantic Search**: Search based on meaning rather than keywords
- **Cosine Similarity**: Measure of similarity between vectors
- **FFI**: Foreign Function Interface (Rust-Python integration)

### Appendix B: Performance Benchmarks

| Operation | Current | Target | Notes |
|-----------|---------|--------|-------|
| PDF Processing (10MB) | 3.2s | 2.0s | Optimization needed |
| Embedding Generation (1000 tokens) | 0.8s | 1.0s | Meeting target |
| Vector Search (10k vectors) | 45ms | 100ms | Exceeding target |
| End-to-end Query | 2.5s | 2.0s | Close to target |

### Appendix C: Future Enhancements

1. **Image Processing**: Add support for image embedding and OCR
2. **Multi-modal Search**: Combine text and image embeddings
3. **Fine-tuning**: Custom model training for domain-specific tasks
4. **Graph RAG**: Incorporate knowledge graph for enhanced retrieval
5. **Streaming Ingestion**: Real-time document processing
6. **Multi-language**: Support for non-English documents
7. **Advanced Analytics**: Usage patterns and query analytics dashboard

---

## Document Control

- Version: 1.0
- Last Updated: November 9, 2025
- Next Review: December 9, 2025
- Status: Draft for Review
