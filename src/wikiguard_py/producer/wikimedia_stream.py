"""Connects to the live Wikimedia recentchange SSE stream.

No filtering/business logic here — just "get raw events off the wire".
See normalizer.py for what happens to each raw payload next.
"""

import asyncio
import json
import logging

import httpx
from httpx_sse import aconnect_sse

logger = logging.getLogger(__name__)

# Singular "recentchange", not plural — the plural URL returns 400.
STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

# Wikimedia's User-Agent policy (meta.wikimedia.org/wiki/User-Agent_policy)
# rejects requests without an identifying User-Agent — the default httpx one
# gets a 403.
USER_AGENT = "wikiguard-py/0.1 (educational portfolio project; Handson Backend Bootcamp)"

INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30


async def stream_recentchanges():
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=None, headers=headers) as client:
        async with aconnect_sse(client, "GET", STREAM_URL) as event_source:
            async for sse in event_source.aiter_sse():
                if not sse.data:
                    continue
                yield json.loads(sse.data)


async def stream_recentchanges_with_retry():
    """Like stream_recentchanges, but reconnects with exponential backoff
    instead of dying the moment the connection drops."""
    backoff = INITIAL_BACKOFF_SECONDS
    while True:
        try:
            async for raw_event in stream_recentchanges():
                backoff = INITIAL_BACKOFF_SECONDS
                yield raw_event
        except Exception as exc:
            logger.warning("Wikimedia stream disconnected, retrying in %ss: %s", backoff, exc)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
