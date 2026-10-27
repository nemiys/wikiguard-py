"""Tests for ensure_topic_exists — against the real, already-existing
"wiki-edit-events" topic. Safe to run against the live topic: this
function only checks and creates, it never alters or recreates a topic
that already exists.
"""

from aiokafka.admin import AIOKafkaAdminClient

from wikiguard_py.producer.kafka_publisher import TOPIC
from wikiguard_py.producer.topics import PARTITION_COUNT, ensure_topic_exists

BOOTSTRAP_SERVERS = "localhost:9094"


async def test_topic_exists_after_ensure():
    await ensure_topic_exists(BOOTSTRAP_SERVERS)
    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    await admin.start()
    try:
        topics = await admin.list_topics()
        assert TOPIC in topics
    finally:
        await admin.close()


async def test_ensure_topic_exists_is_idempotent():
    await ensure_topic_exists(BOOTSTRAP_SERVERS)
    await ensure_topic_exists(BOOTSTRAP_SERVERS)  # must not raise


async def test_topic_has_configured_partition_count():
    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    await admin.start()
    try:
        metadata = await admin.describe_topics([TOPIC])
        assert len(metadata[0]["partitions"]) == PARTITION_COUNT
    finally:
        await admin.close()
