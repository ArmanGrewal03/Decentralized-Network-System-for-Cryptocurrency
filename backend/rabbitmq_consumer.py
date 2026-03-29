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
from state import get_blockchain
from blockchain.block import Block

try:
    from wallet import verify_transaction_signature
    from logger import add_event
except ImportError:
    verify_transaction_signature = lambda tx: True
    def add_event(type, msg, level="info"): pass


def _on_message(ch, method, properties, body):
    try:
        data = json.loads(body)
        queue = method.routing_key
        chain = get_blockchain()

        if queue == QUEUE_PENDING_TX:
            add_event("RabbitMQ", f"Received PENDING_TX message: {data.get('id', 'unknown')}", "info")
            if not verify_transaction_signature(data):
                add_event("RabbitMQ", f"Rejected PENDING_TX (Invalid signature): {data.get('id')}", "warning")
                return
            tx_id = data.get("id")
            if tx_id and not any(t.get("id") == tx_id for t in chain.pending_transactions):
                chain.pending_transactions.append(data)
                add_event("RabbitMQ", f"Added transaction {tx_id} to pool via RabbitMQ", "success")
        elif queue == QUEUE_NEW_BLOCKS:
            block = Block.from_dict(data)
            add_event("RabbitMQ", f"Received NEW_BLOCK message: Index {block.index}", "info")
            if len(chain.chain) == block.index:
                chain.chain.append(block)
                chain._save()
                add_event("RabbitMQ", f"Sync: Added block {block.index} via RabbitMQ", "success")
    except Exception as e:
        add_event("RabbitMQ", f"Consumer callback error: {str(e)}", "error")
        print(f"Consumer callback error: {e}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def _run_consumer():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
        )
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue=QUEUE_PENDING_TX, durable=True)
        ch.queue_declare(queue=QUEUE_NEW_BLOCKS, durable=True)
        ch.basic_qos(prefetch_count=1)
        ch.basic_consume(queue=QUEUE_PENDING_TX, on_message_callback=_on_message)
        ch.basic_consume(queue=QUEUE_NEW_BLOCKS, on_message_callback=_on_message)
        ch.start_consuming()
    except Exception as e:
        print(f"RabbitMQ consumer error: {e}")


def start_consumer_background():
    t = threading.Thread(target=_run_consumer, daemon=True)
    t.start()
    print("RabbitMQ consumer started in background")
