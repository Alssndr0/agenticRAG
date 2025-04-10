from sentence_transformers import SentenceTransformer

from utils.load_env import get_env_vars

from ..utils.device import get_device

env_vars = get_env_vars()
EMBED_MODEL_ID = env_vars["EMBED_MODEL_ID"]


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
