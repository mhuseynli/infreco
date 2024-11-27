import logging
import json
import os
import django
from bson import ObjectId

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infreco.settings")
django.setup()

from core.database import db
from core.services.rabbitmq import get_rabbitmq_connection

logger = logging.getLogger(__name__)

def process_event(event_data):
    """
    Process the event received from RabbitMQ.
    """
    try:
        # Directly insert the validated and resolved event into the database
        db.events.insert_one({
            "webshop_id": event_data["webshop_id"],
            "user_id": ObjectId(event_data["user_id"]),
            "product_id": ObjectId(event_data["product_id"]),
            "event_id": ObjectId(event_data["event_id"]),
            "timestamp": event_data["timestamp"],
        })
        logger.info(f"Processed event: {event_data}")

    except Exception as e:
        logger.error(f"Error processing event: {e}")
        # Add retry logic or move to a dead-letter queue as needed

def callback(ch, method, properties, body):
    """
    RabbitMQ callback to process received messages.
    """
    try:
        event_data = json.loads(body)
        process_event(event_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message: {e}")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")

with get_rabbitmq_connection() as connection:
    channel = connection.channel()
    channel.queue_declare(queue="webshop_events", durable=True)
    channel.basic_consume(queue="webshop_events", on_message_callback=callback, auto_ack=True)
    logger.info(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()