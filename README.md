# GeneralRAG

A general-purpose Retrieval-Augmented Generation (RAG) system with an end-to-end pipeline for document processing, enhancement, and knowledge base creation.

## Pipeline Overview

This system consists of three main pipeline stages:

1. **Extract Pipeline**: Processes documents (PDFs), extracts their text, and chunks them into manageable pieces
2. **Enhance Pipeline**: Adds document and chunk-level summaries to improve context retrieval
3. **Knowledge Base Pipeline**: Creates vector (FAISS) and sparse (BM25) indexes for efficient retrieval

## Setup

1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Update the `.env` file with your configuration

## Pipeline Usage

### 1. Extract Pipeline

The Extract Pipeline processes PDF documents, extracts text, and creates optimal chunks for RAG.

```bash
# Basic usage (uses settings from .env file)
python extract/extract_pipeline.py

# Process files from a specific folder
python extract/extract_pipeline.py --input-folder data/raw/documents

# Specify output location
python extract/extract_pipeline.py --output-file data/chunked/my_chunks.json

# Clear previous output file before processing
python extract/extract_pipeline.py --clear-output

# Set custom chunk parameters
python extract/extract_pipeline.py --min-words 150 --max-tokens 512

# Process a single specific file
python extract/extract_pipeline.py --specific-file data/raw/documents/my_doc.pdf
```

Key parameters:
- `--input-folder`: Directory containing PDF documents to process
- `--output-file`: Path to save extracted chunks
- `--clear-output`: Clear the output file before processing (otherwise appends)
- `--min-words`: Minimum words per chunk
- `--max-tokens`: Maximum tokens per chunk
- `--specific-file`: Process only the specified file

### 2. Enhance Pipeline

The Enhance Pipeline enriches extracted chunks with document and chunk-level summaries to improve retrieval relevance.

```bash
# Basic usage (uses settings from .env file)
python enhance/enhance_pipeline.py

# Specify input and output files
python enhance/enhance_pipeline.py --input-file data/chunked/my_chunks.json --output-file data/enhanced/enhanced_chunks.json

# Keep temporary files for debugging
python enhance/enhance_pipeline.py --keep-temp

# Set custom temporary directory
python enhance/enhance_pipeline.py --temp-dir data/temp
```

Key parameters:
- `--input-file`: Path to the extracted chunks JSON file
- `--output-file`: Path to save the enhanced chunks JSON file
- `--temp-dir`: Directory for temporary files during processing
- `--keep-temp`: Keep temporary files after processing (for debugging)

### 3. Knowledge Base Pipeline

The Knowledge Base Pipeline takes enhanced chunks and creates vector (FAISS) and sparse (BM25) indexes for efficient retrieval.

```bash
# Basic usage (uses settings from .env file)
python knowledge_base/kb_pipeline.py

# Specify input file and index name
python knowledge_base/kb_pipeline.py --input data/enhanced/my_chunks.json --index-name my_custom_index

# Create only FAISS vector index (skip BM25)
python knowledge_base/kb_pipeline.py --create-faiss --no-bm25

# Create only BM25 sparse index (skip FAISS)
python knowledge_base/kb_pipeline.py --no-faiss --create-bm25

# Specify custom output directory for indexes
python knowledge_base/kb_pipeline.py --output-dir my_indexes
```

Key parameters:
- `--input`: Path to enhanced chunks JSON file
- `--output-dir`: Directory to store created indexes
- `--index-name`: Base name for the created index
- `--create-faiss/--no-faiss`: Create/skip FAISS vector index
- `--create-bm25/--no-bm25`: Create/skip BM25 sparse index

## Complete End-to-End Process

To process documents through the entire pipeline:

```bash
# 1. Extract and chunk documents
python extract/extract_pipeline.py --input-folder data/raw/documents --output-file data/chunked/extracted_chunks.json --clear-output

# 2. Enhance chunks with summaries
python enhance/enhance_pipeline.py --input-file data/chunked/extracted_chunks.json --output-file data/enhanced/enhanced_chunks.json

# 3. Create knowledge base indexes
python knowledge_base/kb_pipeline.py --input data/enhanced/enhanced_chunks.json
```

After completing these steps, you'll have:
- Chunked documents in `data/chunked/extracted_chunks.json`
- Enhanced chunks with summaries in `data/enhanced/enhanced_chunks.json`
- FAISS and BM25 indexes in the `indexes/` directory

## License

[Your License Information]