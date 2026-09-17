"""Consumer entrypoint: reads WikiEditEvents from Kafka, runs every active rule.

Stage 4 scope: two hardcoded rules, log-only. Dynamic rules loaded from
Postgres arrive in Stage 5.
"""

import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis

from wikiguard_py.domain.evaluators import ThresholdEvaluator, WindowCountEvaluator
from wikiguard_py.domain.models import WikiEditEvent
from wikiguard_py.producer.kafka_publisher import TOPIC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9094"
CONSUMER_GROUP = "wikiguard-consumers"
REDIS_HOST = "localhost"
REDIS_PORT = 6380

# Placeholders until Stage 5 loads real rules from Postgres.
BYTE_THRESHOLD = 300
WINDOW_SECONDS = 300
WINDOW_EDIT_THRESHOLD = 5


async def run() -> None:
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
    )
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    evaluators = [
        ThresholdEvaluator(byte_threshold=BYTE_THRESHOLD),
        WindowCountEvaluator(
            redis=redis,
            rule_id="window-count-default",
            window_seconds=WINDOW_SECONDS,
            edit_count_threshold=WINDOW_EDIT_THRESHOLD,
        ),
    ]

    await consumer.start()
    try:
        async for message in consumer:
            event = WikiEditEvent.model_validate_json(message.value)
            for evaluator in evaluators:
                if await evaluator.evaluate(event):
                    logger.info(
                        "ALERT [%s]: %s changed %d bytes on %s",
                        type(evaluator).__name__,
                        event.user,
                        event.byte_change,
                        event.page_title,
                    )
    finally:
        await consumer.stop()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(run())
