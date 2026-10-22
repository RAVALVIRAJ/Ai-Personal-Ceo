import logging
import time
from app.services.extraction_service import ExtractedItem

logger = logging.getLogger(__name__)


class PendingConversationItem:

    def __init__(self, item: ExtractedItem, expires_at: float):
        self.item = item
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class ConversationService:
    """
    In-memory store for pending partial items per conversation_id.
    Entries expire after 10 minutes (600 seconds) by default.
    """

    def __init__(self, ttl_seconds: int = 600):
        self._store: dict[str, PendingConversationItem] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, conversation_id: str | None) -> ExtractedItem | None:
        if not conversation_id:
            return None
        self._cleanup()
        pending = self._store.get(conversation_id)
        if pending:
            if pending.is_expired():
                del self._store[conversation_id]
                return None
            return pending.item
        return None

    def set(self, conversation_id: str | None, item: ExtractedItem) -> None:
        if not conversation_id:
            return
        self._cleanup()
        self._store[conversation_id] = PendingConversationItem(
            item=item,
            expires_at=time.time() + self.ttl_seconds,
        )

    def remove(self, conversation_id: str | None) -> None:
        if conversation_id and conversation_id in self._store:
            del self._store[conversation_id]

    def _cleanup(self) -> None:
        now = time.time()
        expired_keys = [k for k, v in self._store.items() if now > v.expires_at]
        for k in expired_keys:
            del self._store[k]


conversation_service = ConversationService(ttl_seconds=600)
