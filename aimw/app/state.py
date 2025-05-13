_retriever = None
_inference_client = None


def set_retriever(retriever):
    """
    Sets the global retriever instance.

    Args:
        retriever: The retriever instance to be set.
    """
    global _retriever
    _retriever = retriever


def set_inference_client(client):
    """
    Sets the global inference client instance.

    Args:
        client: The inference client instance to be set.
    """
    global _inference_client
    _inference_client = client


def get_retriever():
    """
    Retrieves the global retriever instance.

    Returns:
        The global retriever instance.
    """
    return _retriever


def get_inference_client():
    """
    Retrieves the global inference client instance.

    Returns:
        The global inference client instance.
    """
    return _inference_client
