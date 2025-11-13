import pika
from typing import Callable

def create_rabbit_connection(url: str, queue_name: str, on_message: Callable):
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)
    return connection, channel
