import os
import sys

from sentence_transformers import SentenceTransformer

# Add the parent directory to sys.path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.device import get_device
from utils.load_env import get_env_vars

env_vars = get_env_vars()
EMBED_MODEL_ID = env_vars.get("EMBED_MODEL_ID", "Alibaba-NLP/gte-Qwen2-7B-instruct")


def load_embedding_model(model_name=EMBED_MODEL_ID):
    """
    Load a SentenceTransformer model on the appropriate device.

    Args:
        model_name (str): The name of the pretrained model to load.

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    device = get_device()
    model_kwargs = {"device": device}
    return SentenceTransformer(model_name, **model_kwargs)
