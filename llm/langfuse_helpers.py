import logging

from langfuse import Langfuse

from config import settings

logger = logging.getLogger(__name__)


def create_langfuse_client() -> Langfuse | None:
    """Create a Langfuse client if credentials are configured, otherwise return None."""
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning("Langfuse credentials not configured — tracing disabled")
        return None
    return Langfuse()


def update_and_flush_trace(langfuse_client, user_id, model, provider):
    """Update the current Langfuse trace with provider metadata."""
    langfuse_client.update_current_trace(
        name=settings.app_name,
        user_id=user_id,
        metadata={"model": model, "provider": provider},
    )
    langfuse_client.flush()
