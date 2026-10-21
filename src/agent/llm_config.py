"""
llm_config.py — Centralized LLM Provider & Model Configuration

Configures primary and secondary LLM models dynamically from .env for
Google ADK and LiteLLM integration.
"""

import os
import logging
import dotenv
import litellm

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

PRIMARY_LLM_PROVIDER = os.getenv("PRIMARY_LLM_PROVIDER", "groq")
PRIMARY_LLM_MODEL = os.getenv("PRIMARY_LLM_MODEL", "openai/gpt-oss-120b")
PRIMARY_LLM_API_KEY = os.getenv("PRIMARY_LLM_API_KEY")
PRIMARY_LLM_BASE_URL = os.getenv("PRIMARY_LLM_BASE_URL", "https://api.groq.com/openai/v1")

SECONDARY_LLM_PROVIDER = os.getenv("SECONDARY_LLM_PROVIDER", "groq")
SECONDARY_LLM_MODEL = os.getenv("SECONDARY_LLM_MODEL", "qwen/qwen3.8-27b")
SECONDARY_LLM_API_KEY = os.getenv("SECONDARY_LLM_API_KEY")
SECONDARY_LLM_BASE_URL = os.getenv("SECONDARY_LLM_BASE_URL", "https://api.groq.com/openai/v1")

if PRIMARY_LLM_API_KEY and not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = PRIMARY_LLM_API_KEY

litellm.drop_params = True


_orig_acompletion = litellm.acompletion
_orig_completion = litellm.completion

def _sanitize_messages(kwargs: dict):
    if "messages" in kwargs and isinstance(kwargs["messages"], list):
        for msg in kwargs["messages"]:
            if isinstance(msg, dict):
                msg.pop("reasoning_content", None)
                msg.pop("reasoning", None)

async def _patched_acompletion(*args, **kwargs):
    _sanitize_messages(kwargs)
    return await _orig_acompletion(*args, **kwargs)

def _patched_completion(*args, **kwargs):
    _sanitize_messages(kwargs)
    return _orig_completion(*args, **kwargs)

litellm.acompletion = _patched_acompletion
litellm.completion = _patched_completion

def _format_model_name(provider: str, model: str) -> str:
    if not provider or not model:
        return model or ""
    if model.startswith(f"{provider}/"):
        return model
    return f"{provider}/{model}"

PRIMARY_MODEL_NAME = _format_model_name(PRIMARY_LLM_PROVIDER, PRIMARY_LLM_MODEL)
SECONDARY_MODEL_NAME = _format_model_name(SECONDARY_LLM_PROVIDER, SECONDARY_LLM_MODEL)

logger.info("[LLMConfig] Initialized Primary Model: %s, Secondary Model: %s", PRIMARY_MODEL_NAME, SECONDARY_MODEL_NAME)
