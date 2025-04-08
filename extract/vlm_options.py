from docling.datamodel.pipeline_options import (
    PictureDescriptionApiOptions,
)

from utils.load_env import get_env_vars


def openai_vlm_options(model=None):
    env_vars = get_env_vars()
    openai_api_key = env_vars["OPENAI_API_KEY"]
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    # Use environment variables with defaults
    api_url = env_vars["OPENAI_API_URL"]
    model = model or env_vars["OPENAI_MODEL"]
    max_tokens = env_vars["OPENAI_MAX_TOKENS"]

    options = PictureDescriptionApiOptions(
        url=api_url,
        # Use correct keys expected by OpenAI
        params={"model": model, "max_tokens": max_tokens},
        headers={
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json",
        },
        prompt=env_vars["VLM_PROMPT"],
        timeout=120,
    )
    return options
