from sentence_transformers import SentenceTransformer

from ..utils.device import get_device


def load_embedding_model(model_name="intfloat/multilingual-e5-large-instruct"):
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
