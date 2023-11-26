import pika
import json


def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))


def send_event_to_queue(event_data):
    with get_rabbitmq_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue='webshop_events', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='webshop_events',
            body=json.dumps(event_data),
            properties=pika.BasicProperties(delivery_mode=2))
