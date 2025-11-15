# Debug Logging System

A comprehensive debug logging system designed specifically for the PDF processing pipeline, providing detailed tracing, performance metrics, and visual debugging aids. **The system automatically detects production environments and minimizes logging overhead for optimal production performance.**

## Features

### 🔍 Specialized Debug Logging
- **Stage-based logging**: Track processing stages with automatic indentation
- **Data preview**: Inspect data structures with intelligent previews
- **Performance tracking**: Automatic timing and performance analysis
- **Error context**: Enhanced error reporting with full context

### 🏭 **Production Environment Detection (NEW)**
- **Automatic detection**: Recognizes production environments via environment variables
- **Smart defaults**: Debug logging automatically disabled in production
- **Performance optimized**: Zero debug overhead when production detected
- **Override capability**: Manual control when needed

### 📊 Specialized Content Logging
- **Image processing**: Detailed image extraction logging with dimensions, formats, and sizes
- **Table processing**: Table structure logging with row/column counts and headers
- **Equation processing**: Mathematical content logging with LaTeX preview
- **Text chunking**: Chunk analysis with size and overlap information

### ⏱️ Performance Analysis
- **Operation timing**: Automatic timing of operations and stages
- **Performance reports**: JSON reports with statistical analysis
- **Memory tracking**: Monitor memory usage during processing
- **Bottleneck identification**: Identify slow operations

## Production Environment Detection

The debug logging system automatically detects production environments and adjusts its behavior accordingly. This ensures optimal performance in production while maintaining full debugging capabilities in development.

### Automatic Detection

The system checks for these common production indicators:

**Environment Variables:**
- `ENVIRONMENT=production` or `ENVIRONMENT=prod`
- `ENV=production` or `ENV=prod`
- `NODE_ENV=production`
- `FLASK_ENV=production`
- `DJANGO_ENV=production`
- `PYTHON_ENV=production`
- `DEBUG=false` or `DEBUG=0` or `DEBUG=no`
- `DEBUG_MODE=false`

**Cloud Platform Indicators:**
- `KUBERNETES_SERVICE_HOST` (Kubernetes deployment)
- `AWS_EXECUTION_ENV` (AWS Lambda)
- `GOOGLE_CLOUD_PROJECT` (Google Cloud)
- `AZURE_FUNCTIONS_ENVIRONMENT` (Azure Functions)

### Production Mode Behavior

When production environment is detected:
- **Debug Level**: Automatically set to "ERROR" (only errors logged)
- **Detailed Logging**: Disabled (no stage, data, or performance logging)
- **Image/Table/Equation Logging**: Disabled
- **Performance Reports**: Disabled
- **Memory Overhead**: Minimized

### Manual Override

You can override automatic detection:

```python
# Force enable debug logging even in production
config = DebugConfig(enabled=True, auto_detect_production=False)

# Force disable debug logging even in development
config = DebugConfig(enabled=False, auto_detect_production=False)

# Use automatic detection (default)
config = DebugConfig()  # enabled=None, auto_detect_production=True
```

### Check Current Environment

```python
from src.core.debug_logger import DebugConfig, is_production

# Quick check
if is_production():
    print("Running in production mode")

# Detailed environment info
config = DebugConfig()
env_info = config.get_environment_info()
print(f"Environment: {env_info['environment_type']}")
print(f"Debug enabled: {env_info['debug_enabled']}")
```


### 1. Basic Usage

```python
from src.core.debug_logger import PDFDebugLogger
from src.processors.pdf_processor import PDFProcessor

# Create PDF processor with debug logging
processor = PDFProcessor(
    debug=True,
    debug_level="DEBUG"
)

# Process a PDF - debug logging is automatic
content = processor.extract_multimodal_content("document.pdf", "doc_1")
```

### 2. Custom Debug Logger

```python
from src.core.debug_logger import PDFDebugLogger

debug_logger = PDFDebugLogger(name="my_debug", level="DEBUG")

# Use context manager for operations
with debug_logger.debug_operation("Custom Operation"):
    debug_logger.debug_stage("Processing step 1")
    debug_logger.debug_data("Input data", my_data)
    # ... your processing code ...
    debug_logger.debug_success("Operation completed")
```

### 3. Advanced Configuration

```python
from src.core.debug_logger import DebugConfig, init_debug_logging

config = DebugConfig(
    enabled=True,
    level="DEBUG",
    log_images=True,
    log_tables=True,
    log_performance=True,
    save_reports=True,
    reports_dir="logs/debug"
)

debug_logger = init_debug_logging(config)
```

## Debug Logger Methods

### Core Logging Methods

- **`debug_stage(stage_name, **kwargs)`**: Log a processing stage
- **`debug_success(stage_name, **kwargs)`**: Log successful completion
- **`debug_error(stage_name, error, **kwargs)`**: Log errors with context
- **`debug_data(data_name, data, preview_length=100)`**: Log data with preview

### Specialized Content Logging

```python
# Image processing
debug_logger.debug_image_processing(
    image_index=1, xref=12345, width=800, height=600,
    format_type="PNG", size_bytes=1024*1024
)

# Table processing
debug_logger.debug_table_processing(
    table_index=1, rows=10, cols=5,
    headers=["Name", "Age", "City"]
)

# Equation processing
debug_logger.debug_equation_processing(
    eq_index=1, eq_type="LaTeX",
    latex_code=r"\\frac{x^2}{y}"
)

# Text chunking
debug_logger.debug_chunking(
    chunk_index=1, chunk_size=500,
    chunk_type="semantic", overlap_size=50
)
```

### Performance Methods

```python
# Manual performance logging
debug_logger.debug_performance("operation_name", duration, **metrics)

# Performance analysis
debug_logger.print_performance_summary()
debug_logger.save_performance_report("performance.json")
```

## Decorators

### @debug_operation
Automatically wrap functions with debug logging:

```python
from src.core.debug_logger import debug_operation

@debug_operation("PDF Text Extraction")
def extract_text(self, file_path):
    # Function automatically logged with timing
    return extracted_text
```

### @timed_operation
Add automatic timing to functions:

```python
from src.core.debug_logger import timed_operation

@timed_operation("PDF Processing")
def process_pdf(file_path):
    # Function automatically timed
    return result
```

## Context Managers

### debug_operation()
Track operations with automatic success/error handling:

```python
with debug_logger.debug_operation("PDF Analysis", file_path=path):
    # Any code here is automatically tracked
    # Success/error logging is automatic
    result = analyze_pdf(path)
```

## Configuration Options

### DebugConfig Parameters

- **`enabled`**: Enable/disable debug logging (default: True)
- **`level`**: Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
- **`log_images`**: Enable image processing logging (default: True)
- **`log_tables`**: Enable table processing logging (default: True)
- **`log_equations`**: Enable equation processing logging (default: True)
- **`log_chunking`**: Enable text chunking logging (default: True)
- **`log_performance`**: Enable performance tracking (default: True)
- **`save_reports`**: Auto-save performance reports (default: False)
- **`reports_dir`**: Directory for reports (default: "logs/debug")

## Output Examples

### Console Output
```
🚀 Starting PDF Multimodal Content Extraction | file_path=document.pdf
  🔄 Open PDF for multimodal extraction | document_id=doc_1
  📊 PDF Document: PyMuPDFDocument(5) pages = 'Document with 5 pages'
  🚀 Starting Extract document hierarchy
    ✅ Extract document hierarchy completed | duration=0.15s
  🚀 Starting Process pages | total_pages=5
    🚀 Starting Process page 1
      🖼️  Image 1: xref=45 | 800x600 | PNG | 1.20MB
      📋 Table 1: 10x5 | headers: Name, Age, City
      ✅ Process page 1 completed | duration=2.45s
  ✅ PDF Multimodal Content Extraction completed | duration=12.34s
```

### Performance Report
```json
{
  "performance_summary": {
    "PDF Text Extraction": {
      "count": 5,
      "total_time": 1.23,
      "average_time": 0.246,
      "min_time": 0.12,
      "max_time": 0.45
    }
  }
}
```

## Integration with PDF Processor

The debug logging system is automatically integrated with the PDF processor when enabled:

```python
# Enable debug logging in PDF processor
processor = PDFProcessor(
    debug=True,                    # Enable debug logging
    debug_level="DEBUG",           # Set logging level
    extract_images=True,
    extract_tables=True
)

# All operations are automatically logged
text = processor.extract_text("document.pdf")
content = processor.extract_multimodal_content("document.pdf", "doc_1")
```

## Best Practices

### 1. Use Appropriate Logging Levels
- **DEBUG**: Detailed tracing for development
- **INFO**: General operation information
- **WARNING**: Potential issues
- **ERROR**: Failures and errors

### 2. Context in Operations
Always provide context in debug operations:

```python
with debug_logger.debug_operation("Process PDF",
                                 file_path=path,
                                 document_id=doc_id):
    # Processing code
```

### 3. Performance Monitoring
Enable performance tracking for optimization:

```python
config = DebugConfig(
    log_performance=True,
    save_reports=True
)
```

### 4. Production vs Development
Disable debug logging in production:

```python
# Development
processor = PDFProcessor(debug=True, debug_level="DEBUG")

# Production
processor = PDFProcessor(debug=False)
```

## Troubleshooting

### Common Issues

1. **No debug output**: Check that logging level is set correctly
2. **Performance reports empty**: Ensure `log_performance=True`
3. **File permissions**: Check write permissions for log directory

### Debug Output Not Showing

```python
import logging

# Configure console logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)
```

### Large Log Files

Configure log rotation:

```python
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'debug.log', maxBytes=10*1024*1024, backupCount=5
)
```

## Demo Script

Run the included demo to see debug logging in action:

```bash
python demo_debug_logging.py
```

This will demonstrate:
- Basic text extraction with logging
- Multimodal content extraction with logging
- Performance analysis
- Manual debug logging examples
- Configuration options

## Files

- **`src/core/debug_logger.py`**: Main debug logging implementation
- **`demo_debug_logging.py`**: Interactive demo script
- **`logs/debug/`**: Default directory for debug reports
- **`logs/debug_demo.log`**: Demo script log output
