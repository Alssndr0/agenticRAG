import time
from abc import ABC, abstractmethod

from app.schemas.ai_models import AiModel
from loguru import logger


class BaseModelLoader(ABC):
    """
    Abstract base class for AI model loaders.
    Provides common logic for loading the model, timing the load, and storing it in a shared registry.
    """

    # Shared registry for all loaded AI models
    ai_models = {}

    def __init__(self, model_name: str, model_dir):
        self.model_name = model_name
        self.model_dir = model_dir

    @abstractmethod
    def load_model(self):
        """
        Implement model-specific loading logic in subclasses.
        """
        pass

    def load(self) -> AiModel:
        """
        Loads the model, records its load time, and stores it in the shared registry.
        """
        logger.info(
            "Loading model '{}' from {}",
            self.model_name,
            self.model_dir,
        )
        start_time = time.time()
        try:
            model = self.load_model()
        except Exception as e:
            logger.error("Error loading {} model: {}", self.model_name, e)
            raise
        elapsed_time = time.time() - start_time

        ai_model_instance = AiModel(
            ai_model_name=self.model_name,
            model=model,
            load_time=elapsed_time,
        )
        self.__class__.ai_models[self.model_name] = ai_model_instance

        logger.info("Loaded {} model in {:.2f} seconds", self.model_name, elapsed_time)
        return ai_model_instance
