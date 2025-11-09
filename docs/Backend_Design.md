# Backend Design Document

## Overview

This document outlines the basic design of the backend for the Retrieval-Augmented Generation (RAG) system. The backend processes various types of input data, converts them into token vectors, and stores them in a vector database. It also facilitates communication with the LLM model and the chatbot frontend.

## System Components

### 1. Data Processing Module

- **Functionality**: Handles various input data types (PDFs, text files, Word documents, Markdown files, Excel sheets, and optionally images).

- **Steps**:
  1. Read and analyze raw data.
  2. Chunk the data into smaller pieces suitable for vectorization.
  3. Ensure efficient data reading, analysis, and chunking.

### 2. Embedding Module

- **Functionality**: Converts data chunks into embeddings using pre-trained models.

- **Details**:
  - Uses free models like BGE Models and Qodo-Embed-1 for proof-of-concept purposes.
  - Embeddings are stored in the vector database.

### 3. Vector Database

- **Technology**: LanceDB

- **Functionality**: Stores token vectors for efficient retrieval.

### 4. Query Processing Module

- **Functionality**: Processes user queries by combining them with context retrieved from the vector database.

- **Steps**:
  1. Retrieve relevant context from the vector database.
  2. Combine the context with the query to form a prompt.

### 5. LLM Integration

- **Technology**: Rust library wrapped for Python integration.

- **Functionality**: Handles prompt processing and response generation.

- **Details**:
  - Accepts a prompt (context + query) as input.
  - Returns the generated response.

### 6. Chatbot Interface

- **Functionality**: Forwards the LLM response to the frontend chatbot.

## Workflow

1. Input data is processed and chunked into smaller pieces.
2. Data chunks are converted into embeddings and stored in the vector database.
3. User queries are combined with context from the vector database to form prompts.
4. Prompts are sent to the LLM for response generation.
5. Responses are forwarded to the chatbot interface.

## Technologies Used

- **Programming Language**: Python
- **Vector Database**: LanceDB
- **Embedding Models**: BGE Models, Qodo-Embed-1
- **LLM Integration**: Rust library with API communication

## Future Considerations

- Extend support for additional data types.
- Optimize the speed of data reading, analysis, and chunking.
- Enhance the scalability of the system for larger datasets.