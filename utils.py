import torch


def get_device():
    """
    Auto-select the best available device for PyTorch operations.

    Returns:
        str: Selected device ('mps', 'cuda', or 'cpu')
    """
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"

    print(f"Using device: {device}")
    return device
