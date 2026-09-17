"""Publishes normalized WikiEditEvents to Kafka.

key = page_title (routing only, for per-page ordering — see ADR-0003).
value = the full WikiEditEvent, self-contained.
"""

from aiokafka import AIOKafkaProducer

from wikiguard_py.domain.models import WikiEditEvent

TOPIC = "wiki-edit-events"


class KafkaEventPublisher:
    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)

    async def start(self) -> None:
        await self._producer.start()

    async def stop(self) -> None:
        await self._producer.stop()

    async def publish(self, event: WikiEditEvent) -> None:
        key = event.page_title.encode("utf-8")
        value = event.model_dump_json().encode("utf-8")
        await self._producer.send_and_wait(TOPIC, value=value, key=key)
