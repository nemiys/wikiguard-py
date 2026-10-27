"""Tests for KafkaEventPublisher — round-trip against real local Kafka.

Uses a dedicated, freshly-created test topic (monkeypatched in place of
the real "wiki-edit-events" topic) so these tests never have to compete
with the live producer/consumer's continuous real traffic on that topic.
"""

import asyncio
import uuid

import pytest
from aiokafka import AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from wikiguard_py.domain.models import WikiEditEvent
from wikiguard_py.producer import kafka_publisher
from wikiguard_py.producer.kafka_publisher import KafkaEventPublisher

BOOTSTRAP_SERVERS = "localhost:9094"


def make_event(**overrides) -> WikiEditEvent:
    defaults = {
        "event_id": "test:1",
        "page_title": "Test Page",
        "wiki": "hewiki",
        "server_name": "he.wikipedia.org",
        "user": "some_user",
        "byte_change": 100,
        "is_bot": False,
        "namespace": 0,
        "revision_id": 1,
        "timestamp": 1_700_000_000,
    }
    defaults.update(overrides)
    return WikiEditEvent(**defaults)


@pytest.fixture
async def test_topic(monkeypatch):
    topic = f"wikiguard-test-{uuid.uuid4().hex[:8]}"
    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    await admin.start()
    await admin.create_topics([NewTopic(name=topic, num_partitions=1, replication_factor=1)])
    await admin.close()

    monkeypatch.setattr(kafka_publisher, "TOPIC", topic)
    yield topic

    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    await admin.start()
    await admin.delete_topics([topic])
    await admin.close()


async def test_publish_round_trip(test_topic):
    publisher = KafkaEventPublisher(bootstrap_servers=BOOTSTRAP_SERVERS)
    await publisher.start()
    consumer = AIOKafkaConsumer(
        test_topic,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        group_id=f"test-{uuid.uuid4().hex[:8]}",
    )
    await consumer.start()
    try:
        await publisher.publish(make_event(event_id="roundtrip:1"))
        message = await asyncio.wait_for(consumer.getone(), timeout=10)
        received = WikiEditEvent.model_validate_json(message.value)
        assert received.event_id == "roundtrip:1"
    finally:
        await consumer.stop()
        await publisher.stop()


async def test_publish_uses_page_title_as_key(test_topic):
    publisher = KafkaEventPublisher(bootstrap_servers=BOOTSTRAP_SERVERS)
    await publisher.start()
    consumer = AIOKafkaConsumer(
        test_topic,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        group_id=f"test-{uuid.uuid4().hex[:8]}",
    )
    await consumer.start()
    try:
        await publisher.publish(make_event(event_id="roundtrip:2", page_title="Specific Page"))
        message = await asyncio.wait_for(consumer.getone(), timeout=10)
        assert message.key == b"Specific Page"
    finally:
        await consumer.stop()
        await publisher.stop()
