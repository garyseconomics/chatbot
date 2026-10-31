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


def update_and_flush_trace(langfuse_client, client_type) -> None:
    """Update the current Langfuse trace with the client type (telegram, discord, cli)."""
    if not langfuse_client:
        return
    # Pending: Client_type is stored in Langfuse's user_id field for now.
    # Change it to a proper client_type field when we redesign the tracking.
    langfuse_client.update_current_trace(name=settings.app_name, user_id=client_type)
    langfuse_client.flush()
