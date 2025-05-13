from string import Template
from typing import Optional
from huggingface_hub import InferenceClient
from loguru import logger
from app.configs.ai_config import get_ai_settings


def format_prompt(
    documents: str,
    question: str,
    template_str: str,
    system_message: str,
    user_prompt: str,
) -> str:
    """Format the prompt using the given documents and question."""
    try:
        # First, substitute the $ placeholders.
        t = Template(template_str)
        intermediate_prompt = t.substitute(
            LLM_SYSTEM_MESSAGE=system_message,
            LLM_PROMPT=user_prompt
        )
        # Then, substitute the curly-brace placeholders.
        final_prompt = intermediate_prompt.format(documents=documents, question=question)
        return final_prompt
    except KeyError as e:
        logger.error("Missing placeholder in template: %s", e)
        raise


def lumera_llm(
    documents: str,
    question: str,
    max_new_tokens: Optional[int] = None,
    stream: Optional[bool] = None,
    client: Optional[InferenceClient] = None,
    custom_system: Optional[str] = None
) -> str:
    """
    Generates a text response using a language model based on provided documents and a question.
    """
    settings = get_ai_settings()

    # Set default parameters if not provided
    if max_new_tokens is None:
        max_new_tokens = settings.LLM_MAX_NEW_TOKENS
    if stream is None:
        stream = settings.LLM_STREAM

    # Fetch template & messages from .env
    template_str = settings.LLM_TEMPLATE
    system_message = settings.LLM_SYSTEM_MESSAGE
    user_prompt = settings.LLM_PROMPT

    # Append custom prompt if provided
    if custom_system is not None:
        system_message += f"\n{custom_system}"

    # Format the prompt with all placeholders
    formatted_prompt = format_prompt(
        documents=documents,
        question=question,
        template_str=template_str,
        system_message=system_message,
        user_prompt=user_prompt,
    )

    # Use provided or fallback client
    if client is None:
        client = InferenceClient(model=settings.LLM_URL)

    try:
        response = client.text_generation(
            formatted_prompt, max_new_tokens=max_new_tokens, stream=stream, temperature=settings.LLM_TEMPERATURE
        )
        return response
    except Exception as e:
        logger.exception("Error during LLM text generation: %s", e)
        raise RuntimeError(f"LLM generation failed: {e}")
