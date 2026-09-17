"""Consumer entrypoint: reads WikiEditEvents from Kafka, runs the Threshold rule.

Stage 3 scope: one hardcoded rule, log-only. Dynamic rules from Postgres and
the Redis-backed Window-Count rule arrive in later stages.
"""

import asyncio
import logging

from aiokafka import AIOKafkaConsumer

from wikiguard_py.domain.evaluators import ThresholdEvaluator
from wikiguard_py.domain.models import WikiEditEvent
from wikiguard_py.producer.kafka_publisher import TOPIC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9094"
CONSUMER_GROUP = "wikiguard-consumers"

# Placeholder until Stage 5 loads real rules from Postgres.
BYTE_THRESHOLD = 300


async def run() -> None:
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
    )
    evaluator = ThresholdEvaluator(byte_threshold=BYTE_THRESHOLD)

    await consumer.start()
    try:
        async for message in consumer:
            event = WikiEditEvent.model_validate_json(message.value)
            if evaluator.evaluate(event):
                logger.info(
                    "ALERT: %s changed %d bytes on %s",
                    event.user,
                    event.byte_change,
                    event.page_title,
                )
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run())
