"""One-time Kafka topic provisioning.

KAFKA_AUTO_CREATE_TOPICS_ENABLE=false in docker-compose.yml on purpose (see
its comment) — Kafka must not be allowed to auto-create the topic with the
default single partition before this code creates it correctly.
"""

from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from wikiguard_py.producer.kafka_publisher import TOPIC

PARTITION_COUNT = 3
REPLICATION_FACTOR = 1


async def ensure_topic_exists(bootstrap_servers: str) -> None:
    admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    await admin.start()
    try:
        existing_topics = await admin.list_topics()
        if TOPIC not in existing_topics:
            new_topic = NewTopic(
                name=TOPIC,
                num_partitions=PARTITION_COUNT,
                replication_factor=REPLICATION_FACTOR,
            )
            await admin.create_topics([new_topic])
    finally:
        await admin.close()
