"""
RabbitMQ consumer for the GradCafe worker.
Processes scrape_new_data and recompute_analytics tasks.
"""
import json
import logging
import os

import pika
import psycopg

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_db():
    """Return a psycopg connection using DATABASE_URL."""
    return psycopg.connect(os.environ["DATABASE_URL"])


def handle_scrape_new_data(conn, payload):  # pylint: disable=unused-argument
    """Fetch new records and insert them into the applicants table."""
    from etl.incremental_scraper import scrape_data  # pylint: disable=import-outside-toplevel
    rows = scrape_data()
    cur = conn.cursor()
    cur.execute(
        "SELECT last_seen FROM ingestion_watermarks WHERE source = %s",
        ("gradcafe",),
    )
    row = cur.fetchone()
    since = row[0] if row else None
    log.info("Scraping since watermark: %s", since)
    inserted = 0
    max_seen = since
    for record in rows:
        cur.execute(
            "INSERT INTO applicants "
            "(university,program,degree,decision,season,"
            "applicant_status,gpa,added_on,result_id,page_scraped) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT (result_id) DO NOTHING",
            (
                record.get("university"), record.get("program"), record.get("degree"),
                record.get("decision"), record.get("season"), record.get("applicant_status"),
                record.get("gpa"), record.get("added_on"), record.get("result_id"),
                record.get("page_scraped"),
            ),
        )
        inserted += 1
        added = record.get("added_on", "")
        if max_seen is None or (added and added > max_seen):
            max_seen = added
    if max_seen:
        cur.execute(
            "INSERT INTO ingestion_watermarks (source, last_seen) "
            "VALUES (%s, %s) "
            "ON CONFLICT (source) DO UPDATE SET last_seen=EXCLUDED.last_seen, "
            "updated_at=now()",
            ("gradcafe", max_seen),
        )
    conn.commit()
    cur.close()
    log.info("Inserted %s rows", inserted)


def handle_recompute_analytics(conn, payload):  # pylint: disable=unused-argument
    """Recompute analytics summaries."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    count = cur.fetchone()[0]
    log.info("Recompute analytics: %s total applicants", count)
    conn.commit()
    cur.close()


TASK_MAP = {
    "scrape_new_data": handle_scrape_new_data,
    "recompute_analytics": handle_recompute_analytics,
}


def on_message(channel, method, properties, body):  # pylint: disable=unused-argument
    """Route incoming messages to the correct handler."""
    try:
        msg = json.loads(body)
        kind = msg.get("kind")
        payload = msg.get("payload", {})
        log.info("Received task: %s", kind)
        handler = TASK_MAP.get(kind)
        if handler is None:
            log.warning("Unknown task kind: %s", kind)
            channel.basic_nack(method.delivery_tag, requeue=False)
            return
        db_conn = get_db()
        try:
            handler(db_conn, payload)
            channel.basic_ack(method.delivery_tag)
        except Exception as exc:  # pylint: disable=broad-except
            log.error("Handler error: %s", exc)
            db_conn.rollback()  # pylint: disable=no-member
            channel.basic_nack(method.delivery_tag, requeue=False)
        finally:
            db_conn.close()  # pylint: disable=no-member
    except Exception as exc:  # pylint: disable=broad-except
        log.error("Message parse error: %s", exc)
        channel.basic_nack(method.delivery_tag, requeue=False)


def main():
    """Start the RabbitMQ consumer."""
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    rmq_conn = pika.BlockingConnection(params)
    channel = rmq_conn.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=on_message)
    log.info("Worker waiting for tasks...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
