import torch
from app.configs.ai_config import get_ai_settings
from app.loaders.base_loader import BaseModelLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from loguru import logger


class BgeEmbeddingsLoader(BaseModelLoader):
    """Loader for the BGE Embeddings model."""

    def __init__(self):
        super().__init__(
            get_ai_settings().EMBEDDING_MODEL,
            get_ai_settings().EMBEDDING_MODEL_DIR,
        )

    def load_model(self):
        return BgeEmbeddings(model_path=self.model_dir)


class BgeEmbeddings:
    def __init__(self, model_path):
        """
        Load the BGE embeddings model.

        Args:
            model_path (Path): The directory path where the BGE model is stored.
        """
        self.model_path = model_path
        # Get a displayable name from the path (if available)
        model_name = model_path.name if hasattr(model_path, "name") else str(model_path)
        logger.info("Provided model path: {}", model_path)

        encode_kwargs = {"normalize_embeddings": True}
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Selected device for embeddings: {}", device)
        model_kwargs = {"device": device}

        try:
            # Instantiate the HuggingFaceBgeEmbeddings model.
            self.embeddings = HuggingFaceBgeEmbeddings(
                model_name=str(model_path),  # Ensure model_path is a string
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
            )
        except Exception as e:
            logger.exception(
                "Failed to load BGE embeddings model '{}'. Error: {}", model_name, e
            )
            raise
