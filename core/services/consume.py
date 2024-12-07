import logging
import json
import os
import django
from bson import ObjectId

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infreco.settings")
django.setup()

from core.database import db
from core.services.rabbitmq import get_rabbitmq_connection
from core.trainers.dynamic_content_based import process_event_with_trainer
from core.trainers.dynamic_collaborative import DynamicCollaborativeTrainer

logger = logging.getLogger(__name__)

PREFERENCE_DECAY_RATE = 0.9  # 10% decay on every update


def update_user_preferences(event_data):
    """
    Dynamically update user preferences based on an event.
    """
    try:
        # Fetch the user profile
        user = db.users.find_one({"_id": ObjectId(event_data["user_id"])})
        if not user:
            raise ValueError(f"User not found: {event_data['user_id']}")

        # Fetch the product details
        product = db.items.find_one({"_id": ObjectId(event_data["product_id"])})
        if not product:
            raise ValueError(f"Product not found: {event_data['product_id']}")

        # Fetch the event type weight
        event_type = db.event_types.find_one({"_id": ObjectId(event_data["event_id"])})
        if not event_type:
            raise ValueError(f"Event type not found: {event_data['event_id']}")

        event_weight = event_type["weight"]
        preferences = user.get("preferences", {})

        # Decay existing preferences
        for key in preferences.keys():
            preferences[key] *= PREFERENCE_DECAY_RATE

        # Update preferences based on product attributes
        for attr in ["categories", "brand"]:  # Attributes to track
            value = product.get(attr)
            if isinstance(value, list):  # Handle attributes with multiple values
                for item in value:
                    preferences[item] = preferences.get(item, 0) + event_weight
            elif value:
                preferences[value] = preferences.get(value, 0) + event_weight

        # Normalize preferences (optional)
        total_weight = sum(preferences.values())
        preferences = {k: v / total_weight for k, v in preferences.items()}

        # Update the user profile in the database
        db.users.update_one(
            {"_id": ObjectId(event_data["user_id"])},
            {"$set": {"preferences": preferences}}
        )
        logger.info(f"Updated preferences for user_id: {event_data['user_id']}")

    except Exception as e:
        logger.error(f"Error updating user preferences: {e}", exc_info=True)


def update_dynamic_collaborative(event_data):
    """
    Dynamically update collaborative filtering data for the webshop.
    """
    try:
        webshop_id = event_data["webshop_id"]
        trainer = DynamicCollaborativeTrainer(webshop_id)
        trainer.process_event(event_data)
        logger.info(f"Dynamic collaborative data updated for webshop_id: {webshop_id}")
    except Exception as e:
        logger.error(f"Error updating dynamic collaborative trainer: {e}", exc_info=True)


def process_event(event_data):
    """
    Process the event received from RabbitMQ.
    """
    try:
        # Store the event in the database
        db.events.insert_one({
            "webshop_id": event_data["webshop_id"],
            "user_id": ObjectId(event_data["user_id"]),
            "product_id": ObjectId(event_data["product_id"]),
            "event_id": ObjectId(event_data["event_id"]),
            "timestamp": event_data["timestamp"],
        })
        logger.info(f"Event processed and stored in database: {event_data}")

        # Update user preferences based on the event
        update_user_preferences(event_data)

        # Update dynamic collaborative filtering model
        update_dynamic_collaborative(event_data)

        # Trigger dynamic content-based training
        process_event_with_trainer(event_data)

    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)


def callback(ch, method, properties, body):
    """
    RabbitMQ callback to process received messages.
    """
    try:
        event_data = json.loads(body)
        process_event(event_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)


def start_consumer():
    """Start consuming messages from RabbitMQ."""
    with get_rabbitmq_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue="webshop_events", durable=True)
        channel.basic_consume(queue="webshop_events", on_message_callback=callback, auto_ack=True)
        logger.info(" [*] Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()


if __name__ == "__main__":
    start_consumer()