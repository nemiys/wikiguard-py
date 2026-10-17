"""Consumer entrypoint: reads WikiEditEvents from Kafka, runs every active rule.

Rules are loaded from Postgres (not hardcoded) and reloaded periodically, so
a rule change takes effect without restarting the consumer.
"""

import asyncio
import logging
import time

from aiokafka import AIOKafkaConsumer

from wikiguard_py.consumer.rule_loader import load_evaluators
from wikiguard_py.consumer.stats import record_event_stats
from wikiguard_py.domain.models import WikiEditEvent
from wikiguard_py.persistence.alerts import record_alert
from wikiguard_py.persistence.database import create_tables
from wikiguard_py.producer.kafka_publisher import TOPIC
from wikiguard_py.redis_client import redis_client
from wikiguard_py.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONSUMER_GROUP = "wikiguard-consumers"

RULE_REFRESH_INTERVAL_SECONDS = 10


async def run() -> None:
    await create_tables()

    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=CONSUMER_GROUP,
    )
    redis = redis_client

    evaluators = await load_evaluators(redis)
    last_refresh = time.monotonic()

    await consumer.start()
    try:
        async for message in consumer:
            if time.monotonic() - last_refresh >= RULE_REFRESH_INTERVAL_SECONDS:
                evaluators = await load_evaluators(redis)
                last_refresh = time.monotonic()

            event = WikiEditEvent.model_validate_json(message.value)
            await record_event_stats(redis, event)

            # Bot edits are routine/automated, not suspicious by nature — they
            # still count toward stream stats above, just never toward rules.
            if event.is_bot:
                continue

            for evaluator in evaluators:
                if await evaluator.evaluate(event):
                    rule_type = type(evaluator).__name__
                    logger.info(
                        "ALERT [%s]: %s changed %d bytes on %s",
                        rule_type,
                        event.user,
                        event.byte_change,
                        event.page_title,
                    )
                    await record_alert(
                        rule_type=rule_type,
                        rule_id=evaluator.rule_id,
                        page_title=event.page_title,
                        wiki=event.wiki,
                        server_name=event.server_name,
                        user=event.user,
                        byte_change=event.byte_change,
                    )
    finally:
        await consumer.stop()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(run())
