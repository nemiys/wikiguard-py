"""Producer entrypoint: wires SSE stream -> normalizer -> Kafka publisher."""

import asyncio
import logging

from wikiguard_py.producer.kafka_publisher import KafkaEventPublisher
from wikiguard_py.producer.normalizer import normalize_recentchange
from wikiguard_py.producer.topics import ensure_topic_exists
from wikiguard_py.producer.wikimedia_stream import stream_recentchanges_with_retry
from wikiguard_py.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run() -> None:
    await ensure_topic_exists(settings.kafka_bootstrap_servers)

    publisher = KafkaEventPublisher(settings.kafka_bootstrap_servers)
    await publisher.start()
    try:
        async for raw in stream_recentchanges_with_retry():
            try:
                event = normalize_recentchange(raw)
            except Exception as exc:
                logger.warning("Skipping malformed event: %s", exc)
                continue

            if event is None:
                continue

            await publisher.publish(event)
            logger.info("Published %s", event.event_id)
    finally:
        await publisher.stop()


if __name__ == "__main__":
    asyncio.run(run())
