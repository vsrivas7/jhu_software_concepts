"""
RabbitMQ publisher for the GradCafe web app.
Publishes tasks to the durable 'tasks' exchange/queue.
"""
import json
import os
from datetime import datetime

import pika

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel():
    """Open a RabbitMQ connection and declare durable exchange/queue."""
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    channel = conn.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    return conn, channel


def publish_task(kind, payload=None, headers=None):
    """Publish a task message to RabbitMQ."""
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.utcnow().isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")
    conn, channel = _open_channel()
    try:
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers=headers or {},
            ),
            mandatory=False,
        )
    finally:
        conn.close()
