import json
import threading

import pika

from config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    QUEUE_PENDING_TX,
    QUEUE_NEW_BLOCKS,
)

try:
    from logger import add_event
except ImportError:
    def add_event(type, msg, level="info"): pass

_connection = None
_channel = None
_lock = threading.Lock()


def _get_channel():
    global _connection, _channel
    with _lock:
        if _channel is not None and _channel.is_open:
            return _channel
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
        )
        _connection = pika.BlockingConnection(params)
        _channel = _connection.channel()
        _channel.queue_declare(queue=QUEUE_PENDING_TX, durable=True)
        _channel.queue_declare(queue=QUEUE_NEW_BLOCKS, durable=True)
        return _channel


def publish_transaction(tx: dict) -> None:
    try:
        ch = _get_channel()
        ch.basic_publish(
            exchange="",
            routing_key=QUEUE_PENDING_TX,
            body=json.dumps(tx),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        add_event("RabbitMQ", f"Published PENDING_TX: {tx.get('id', 'unknown')}", "info")
    except Exception as e:
        add_event("RabbitMQ", f"Publish transaction error: {str(e)}", "error")
        print(f"RabbitMQ publish_transaction error: {e}")


def publish_block(block: dict) -> None:
    try:
        ch = _get_channel()
        ch.basic_publish(
            exchange="",
            routing_key=QUEUE_NEW_BLOCKS,
            body=json.dumps(block),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        add_event("RabbitMQ", f"Published NEW_BLOCK: Index {block.get('index', 'unknown')}", "info")
    except Exception as e:
        add_event("RabbitMQ", f"Publish block error: {str(e)}", "error")
        print(f"RabbitMQ publish_block error: {e}")
