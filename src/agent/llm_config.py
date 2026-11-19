import os
import logging
from dotenv import load_dotenv
import litellm

load_dotenv()

logger = logging.getLogger(__name__)

# Primary LLM
PRIMARY_PROVIDER = os.getenv("PRIMARY_LLM_PROVIDER", "groq")
PRIMARY_MODEL = os.getenv("PRIMARY_LLM_MODEL", "openai/gpt-oss-120b")
PRIMARY_LLM_API_KEY = os.getenv("PRIMARY_LLM_API_KEY")
PRIMARY_LLM_BASE_URL = os.getenv("PRIMARY_LLM_BASE_URL")

# Secondary LLM
SECONDARY_PROVIDER = os.getenv("SECONDARY_LLM_PROVIDER", "groq")
SECONDARY_MODEL = os.getenv("SECONDARY_LLM_MODEL", "qwen/qwen3.8-27b")
SECONDARY_LLM_API_KEY = os.getenv("SECONDARY_LLM_API_KEY")
SECONDARY_LLM_BASE_URL = os.getenv("SECONDARY_LLM_BASE_URL")

# LiteLLM configuration
litellm.drop_params = True

# Remove unsupported reasoning fields
def clean_messages(kwargs):
    messages = kwargs.get("messages", [])

    for message in messages:
        message.pop("reasoning_content", None)
        message.pop("reasoning", None)

# Wrap LiteLLM calls
_original_async = litellm.acompletion
_original_sync = litellm.completion

async def async_completion(*args, **kwargs):
    clean_messages(kwargs)
    return await _original_async(*args, **kwargs)

def sync_completion(*args, **kwargs):
    clean_messages(kwargs)
    return _original_sync(*args, **kwargs)

litellm.acompletion = async_completion
litellm.completion = sync_completion

# Final model names
PRIMARY_MODEL_NAME = f"{PRIMARY_PROVIDER}/{PRIMARY_MODEL}"
SECONDARY_MODEL_NAME = f"{SECONDARY_PROVIDER}/{SECONDARY_MODEL}"

logger.info("Primary LLM: %s", PRIMARY_MODEL_NAME)
logger.info("Secondary LLM: %s", SECONDARY_MODEL_NAME)
