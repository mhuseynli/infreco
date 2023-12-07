import logging
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infreco.settings')
django.setup()

from core.database import db
from core.services.rabbitmq import get_rabbitmq_connection

print("Consume started...")
logger = logging.getLogger(__name__)


def get_or_create_user(webshop_id, external_id, attributes):
    user = db.users.find_one({'external_id': external_id, 'webshop_id': webshop_id})
    if user:
        db.users.update_one({'_id': user['_id']}, {'$set': {'attributes': attributes}})
        return user['_id']
    else:
        user_data = {'webshop_id': webshop_id, 'external_id': external_id, 'attributes': attributes}
        inserted_user = db.users.insert_one(user_data)
        return inserted_user.inserted_id


def get_or_create_item(webshop_id, external_id, attributes):
    item = db.items.find_one({'external_id': external_id, 'webshop_id': webshop_id})
    if item:
        db.items.update_one({'_id': item['_id']}, {'$set': {'attributes': attributes}})
        return item['_id']
    else:
        item_data = {'webshop_id': webshop_id, 'external_id': external_id, 'attributes': attributes}
        inserted_item = db.items.insert_one(item_data)
        return inserted_item.inserted_id


def process_event(event_data):
    try:
        # Extract user and item data from the event
        user_data = event_data['user']
        item_data = event_data['item']

        # Handle user and item data
        user_id = get_or_create_user(event_data['webshop_id'], user_data['id'], user_data['attributes'])
        item_id = get_or_create_item(event_data['webshop_id'], item_data['id'], item_data['attributes'])

        # Insert the event data into the database
        event_to_insert = {
            'webshop_id': event_data['webshop_id'],
            'user_id': user_id,
            'item_id': item_id,
            'event_type': event_data['event_type'],
            'timestamp': event_data['timestamp']
        }
        db.events.insert_one(event_to_insert)
        logger.info(f"Processed event: {event_data}")
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        # Implement retry logic or move to dead-letter queue


def callback(ch, method, properties, body):
    event_data = json.loads(body)
    process_event(event_data)


with get_rabbitmq_connection() as connection:
    channel = connection.channel()
    channel.queue_declare(queue='webshop_events', durable=True)
    channel.basic_consume(queue='webshop_events', on_message_callback=callback, auto_ack=True)
    logger.info(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
