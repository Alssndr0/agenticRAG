# GeneralRAG

A general-purpose Retrieval-Augmented Generation (RAG) system with an end-to-end pipeline for document processing, enhancement, and knowledge base creation.

## Pipeline Overview

This system consists of four main pipeline stages:

1. **Extract Pipeline**: Processes documents (PDFs), extracts their text, and chunks them into manageable pieces
2. **Enhance Pipeline**: Adds document and chunk-level summaries to improve context retrieval
3. **Knowledge Base Pipeline**: Creates vector (FAISS) and sparse (BM25) indexes for efficient retrieval
4. **Graph Pipeline**: Extracts entities and relationships to create a Neo4j knowledge graph

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

### 4. Graph Pipeline

The Graph Pipeline extracts entity and relationship data from documents and creates a knowledge graph in Neo4j.

#### 1. Entity-Relationship Extraction

The first step extracts named entities and their relationships from the enhanced chunks.

```bash
# Basic usage (uses settings from .env file)
python graph/ent_rel_extraction.py

# Specify custom input and output files
python graph/ent_rel_extraction.py --input-file data/enhanced/custom_chunks.json --output-file data/graph/custom_graph_data.json
```

Key features:
- Identifies various entity types (organizations, people, markets, products, etc.)
- Extracts relationships between entities with attributes
- Merges and deduplicates entities and relationships across chunks
- Incrementally saves to a single JSON file to prevent data loss

#### 2. Neo4j Graph Creation

The second step creates a Neo4j graph database from the extracted entity and relationship data.

```bash
# Basic usage (uses default paths)
python graph/create_neo4j.py

# Use a custom input file
python graph/create_neo4j.py --input data/graph/custom_graph_data.json

# Clear the database before importing
python graph/create_neo4j.py --clear
```

Key features:
- Creates entity nodes with appropriate labels based on entity types
- Creates relationships with attributes and strength metrics
- Preserves all attributes for rich querying capabilities
- Adds context information as a special node

### Neo4j Configuration

To use the Neo4j functionality, add the following to your `config.ini` file:

```ini
[neo4j]
NEO4J_URI = bolt://localhost:7687
NEO4J_USERNAME = neo4j
NEO4J_PASSWORD = your_password
```

Alternatively, you can set these as environment variables:
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

### Querying the Knowledge Graph

Once you've created your Neo4j graph database, you can explore it using the Neo4j Browser or Cypher queries:

```cypher
// Find all organization entities
MATCH (org:organization) RETURN org LIMIT 10

// Find relationships between organizations
MATCH (org1:organization)-[r]->(org2:organization) 
RETURN org1.name, type(r), r.strength, org2.name

// Find entities with specific attributes
MATCH (e:Entity) 
WHERE e.rating IS NOT NULL
RETURN e.name, e.rating, e.entity_type
```

## Complete End-to-End Process

To process documents through the entire pipeline:

```bash
# 1. Extract and chunk documents
python extract/extract_pipeline.py --input-folder data/raw/documents --output-file data/chunked/extracted_chunks.json --clear-output

# 2. Enhance chunks with summaries
python enhance/enhance_pipeline.py --input-file data/chunked/extracted_chunks.json --output-file data/enhanced/enhanced_chunks.json

# 3. Create knowledge base indexes
python knowledge_base/kb_pipeline.py --input data/enhanced/enhanced_chunks.json

# 4. Extract entity-relationship data and create Neo4j graph
python graph/ent_rel_extraction.py
python graph/create_neo4j.py --clear
```

After completing these steps, you'll have:
- Chunked documents in `data/chunked/extracted_chunks.json`
- Enhanced chunks with summaries in `data/enhanced/enhanced_chunks.json`
- FAISS and BM25 indexes in the `indexes/` directory
- Entity-relationship data in `data/graph/neo4j_data.json`
- A Neo4j knowledge graph populated with entities and relationships

## Querying the Knowledge Base

Once you've created your knowledge base indexes, you can query them using the hybrid retrieval system:

```bash
# Basic usage - will prompt for a question
python rag_query.py

# Pass a question as a command-line argument
python rag_query.py "What is the debt maturity profile for Engie Brazil?"
```

The hybrid retrieval system combines both vector search (FAISS) and keyword search (BM25) for more reliable and comprehensive results. It:
1. Retrieves relevant documents from both indexes
2. Deduplicates results
3. Formats the context for the LLM
4. Generates a response with citations to source documents

### Configuration

Configure the querying system by setting the following environment variables in your `.env` file:

```
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Use models like gpt-3.5-turbo, gpt-4-turbo, gpt-4o-mini

# Embedding Model Configuration
EMBED_MODEL_ID=Alibaba-NLP/gte-Qwen2-7B-instruct

# Retrieval Configuration
FAISS_INDEX_PATH=/path/to/your/faiss/index
BM25_INDEX_PATH=/path/to/your/bm25/index

# Retrieval Parameters
DEFAULT_ALPHA=0.7  # Weight between FAISS and BM25 (1.0 = only FAISS, 0.0 = only BM25)
DEFAULT_K=5  # Number of documents to retrieve
```

For the `OPENAI_MODEL` variable, make sure to use a model name that is available to your OpenAI account. Common options include:
- `gpt-3.5-turbo` - Faster and less expensive
- `gpt-4-turbo` - More capable but more expensive
- `gpt-4o-mini` - Good balance of capability and cost

### Advanced Usage

You can also use the retrieval components programmatically in your own applications:

```python
from retrieval.generation import initialize_embeddings_model, initialize_retriever, generate_response

# Initialize components
embeddings_model = initialize_embeddings_model()
retriever = initialize_retriever(embeddings_model=embeddings_model)

# Generate a response
question = "What is the debt maturity profile for Engie Brazil?"
response = generate_response(
    question=question,
    retriever=retriever,
    model="gpt-4o",  # OpenAI model to use
    k=5,             # Number of documents to retrieve
    alpha=0.7        # Weight between FAISS (alpha) and BM25 (1-alpha)
)

print(response)
```

## Neo4j Knowledge Graph

The Graph Pipeline extracts entity and relationship data from documents and creates a knowledge graph in Neo4j.

### 1. Entity-Relationship Extraction

The first step extracts named entities and their relationships from the enhanced chunks.

```bash
# Basic usage (uses settings from .env file)
python graph/ent_rel_extraction.py

# Specify custom input and output files
python graph/ent_rel_extraction.py --input-file data/enhanced/custom_chunks.json --output-file data/graph/custom_graph_data.json
```

Key features:
- Identifies various entity types (organizations, people, markets, products, etc.)
- Extracts relationships between entities with attributes
- Merges and deduplicates entities and relationships across chunks
- Incrementally saves to a single JSON file to prevent data loss

### 2. Neo4j Graph Creation

The second step creates a Neo4j graph database from the extracted entity and relationship data.

```bash
# Basic usage (uses default paths)
python graph/create_neo4j.py

# Use a custom input file
python graph/create_neo4j.py --input data/graph/custom_graph_data.json

# Clear the database before importing
python graph/create_neo4j.py --clear
```

Key features:
- Creates entity nodes with appropriate labels based on entity types
- Creates relationships with attributes and strength metrics
- Preserves all attributes for rich querying capabilities
- Adds context information as a special node

### Neo4j Configuration

To use the Neo4j functionality, add the following to your `config.ini` file:

```ini
[neo4j]
NEO4J_URI = bolt://localhost:7687
NEO4J_USERNAME = neo4j
NEO4J_PASSWORD = your_password
```

Alternatively, you can set these as environment variables:
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

### Querying the Knowledge Graph

Once you've created your Neo4j graph database, you can explore it using the Neo4j Browser or Cypher queries:

```cypher
// Find all organization entities
MATCH (org:organization) RETURN org LIMIT 10

// Find relationships between organizations
MATCH (org1:organization)-[r]->(org2:organization) 
RETURN org1.name, type(r), r.strength, org2.name

// Find entities with specific attributes
MATCH (e:Entity) 
WHERE e.rating IS NOT NULL
RETURN e.name, e.rating, e.entity_type
```

## License

[Your License Information]