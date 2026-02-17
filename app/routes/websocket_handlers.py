"""
Stub websocket_handlers module.
Imported by app.__init__ to register WebSocket-related handlers. In this
stub we simply log that realtime features are disabled or handled elsewhere.
"""
import logging

logger = logging.getLogger(__name__)
logger.info("websocket_handlers stub loaded – no explicit handlers to register.")
