from functools import lru_cache
from pathlib import Path

from app.configs.base_config import BASE_DIR, BaseConfig, get_base_config


class AiConfig(BaseConfig):
    model_config = {"env_file": get_base_config().AI_CONFIG_FILE}


class AISettings(AiConfig):
    EMBEDDING_MODEL: str = "Alibaba-NLP/gte-Qwen2-7B-instruct"
    EMBEDDING_MODEL_VERSION: str = "v0.0.1"
    EMBEDDING_MODEL_DIR: Path = (
        BASE_DIR / "resources" / "ai-models" / EMBEDDING_MODEL_VERSION / EMBEDDING_MODEL
    )

    SUMMARISE_MODEL: str = "gpt-4o-mini"
    SUMMARISE_DOCUMENT_PROMPT: str = (
        "Give a short succinct description of the overall document for the purposes of improving search retrieval. \
Answer only with a very succinct summary and nothing else."
    )
    SUMMARISE_DOCUMENT_INPUT_WORDS: int = 1000
    SUMMARISE_CHUNK_PROMPT: int = (
        "Provide only a very short, succinct context summary for the target text to improve its searchability. \
Start with 'This chunk details...'"
    )
    SUMMARISE_CHUNK_MODEL_MAX_INPUT_TOKENS: int = 1000

    LLM_URL: str = "http://127.0.0.1:1234/v1/chat/completions"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_ENDPOINT: str = LLM_URL + "/" + LLM_MODEL

    VLM_PROMPT: str = "If this image is a table or a chart, provide a detailed explanation \
of the insight it wants to convey and extract all the relevant data into a markdown format. \
If it is not a table or a chart, just output 'generic image', only these two words, without any additional text."

    LLM_SYSTEM_MESSAGE: str = (
        "Provide an answer to the original question, based on the documentation you are given. "
        "If you don't find any relevant information to answer the original question, just say that you couldn't find any mention of that in the provided documentation."
    )

    LLM_PROMPT: str = (
        "Start Documentation\n{documents}\nEnd Documentation\n{question}\n"
        "Don't make any assumptions or reflections, only extract the information as it appears in the document. "
        "Answer in the form of 'We', since we are company answering customers questions."
    )

    LLM_MAX_NEW_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.1
    LLM_SEED: int = 1234
    LLM_STREAM: bool = True


@lru_cache()
def get_ai_settings() -> AISettings:
    return AISettings()
