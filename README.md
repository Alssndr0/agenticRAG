# generalRAG

## Embedding Function

This repository includes an implementation of embeddings using the `sentence-transformers` library with the `intfloat/multilingual-e5-large-instruct` model.

### Usage

```python
from embeddings import get_e5_embedder
from utils import get_device

# Get the embedding function
embedder = get_e5_embedder()

# Get the optimal device for your environment
device = get_device()

# Use the embedding function with your graph storage
graph_storage = YourGraphStorageImplementation(
    namespace="your-namespace",
    global_config={},
    embedding_func=embedder
)

# Or use it directly (async)
import asyncio

async def embed_example():
    texts = ["This is a sample text", "Another example"]
    embeddings = await embedder(texts)
    print(embeddings.shape)  # Should be (2, 1024)

asyncio.run(embed_example())
```

### Device Selection

For reusing device selection in other scripts:

```python
from utils import get_device

# Get the optimal device for your environment
device = get_device()  # Returns 'mps', 'cuda', or 'cpu' depending on availability

# Use the device in your code
model = YourModel(device=device)
```

### Requirements

Make sure to install the required packages:

```
pip install sentence-transformers torch
```