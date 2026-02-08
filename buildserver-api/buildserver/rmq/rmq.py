"""RabbitMQ connection, producer, and consumer classes"""

import logging
from typing import Callable
import time

import pika
import pika.channel
import pika.spec

from buildserver.config import Config

config = Config()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


class RabbitMQConnection:
    """Base class providing shared RabbitMQ connection parameters."""

    RECONNECT_DELAY = 5  # seconds

    def __init__(self):
        self._parameters = self._get_connection_parameters()

    @staticmethod
    def _get_connection_parameters() -> pika.ConnectionParameters:
        """Build connection parameters from application config."""
        credentials = pika.PlainCredentials(
            config.RABBITMQ_USER, str(config.RABBITMQ_PASSWORD)
        )
        return pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            credentials=credentials,
        )


class RabbitMQProducer(RabbitMQConnection):
    """Publishes messages to a RabbitMQ queue using a blocking connection."""

    def publish(self, queue: str, body: bytes) -> None:
        """Publish a message to the specified queue.

        Opens a blocking connection, declares the queue, publishes,
        and closes the connection.

        Args:
            queue: The queue name to publish to.
            body: The message body as bytes.
        """
        connection = pika.BlockingConnection(self._parameters)
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()


class RabbitMQConsumer(RabbitMQConnection):
    """Consumes messages from a RabbitMQ queue using a select connection with auto-reconnect."""

    def __init__(self):
        super().__init__()
        self._connection: pika.SelectConnection | None = None
        self._channel: pika.channel.Channel | None = None
        self._stopping = False
        self._queue: str | None = None
        self._on_message: Callable[[bytes], None] | None = None
        self._prefetch_count: int = 1

    def start(
        self, queue: str, on_message: Callable[[bytes], None], prefetch_count: int = 1
    ) -> None:
        """Connect to RabbitMQ and begin consuming from the given queue.

        Blocks the calling thread. Automatically reconnects on connection loss.

        Args:
            queue: The queue name to consume from.
            on_message: Callback that receives the raw message body as bytes.
                Messages are acked on success and nacked on exception.
            prefetch_count: Max unacked messages to allow (limits concurrency).
        """
        self._queue = queue
        self._on_message = on_message
        self._prefetch_count = prefetch_count
        while not self._stopping:
            self._connect()
            self._connection.ioloop.start()
            if not self._stopping:
                logger.info("Reconnecting in %d seconds...", self.RECONNECT_DELAY)
                time.sleep(self.RECONNECT_DELAY)

    def stop(self) -> None:
        """Gracefully stop consuming and close the connection. Thread-safe."""
        logger.info("Stopping RabbitMQ connection...")
        self._stopping = True
        if self._connection and self._connection.is_open:
            self._connection.ioloop.add_callback_threadsafe(self._shutdown)

    def _shutdown(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.close()
        if self._connection and self._connection.is_open:
            self._connection.close()

    def _connect(self) -> None:
        logger.info(
            "Connecting to RabbitMQ host=%s port=%s user=%s",
            self._parameters.host,
            self._parameters.port,
            self._parameters.credentials.username,
        )
        try:
            self._connection = pika.SelectConnection(
                parameters=self._parameters,
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_open_error,
                on_close_callback=self._on_connection_closed,
            )
        except RuntimeError as exc:
            logger.error("Gotcha! %s", exc)

    def _on_connection_open(self, connection: pika.SelectConnection) -> None:
        logger.info("Connection opened")
        connection.channel(on_open_callback=self._on_channel_open)

    def _on_connection_open_error(
        self, connection: pika.SelectConnection, error: Exception
    ) -> None:
        logger.error("Connection open failed: %s", error)
        connection.ioloop.stop()

    def _on_connection_closed(
        self, connection: pika.SelectConnection, reason: Exception
    ) -> None:
        self._channel = None
        if not self._stopping:
            logger.warning("Connection closed unexpectedly: %s", reason)
        else:
            logger.info("Connection closed")
        connection.ioloop.stop()

    def _on_channel_open(self, channel: pika.channel.Channel) -> None:
        logger.info("Channel opened")
        self._channel = channel
        # Limit unacked messages to avoid overwhelming workers
        self._channel.basic_qos(prefetch_count=self._prefetch_count)
        self._channel.queue_declare(
            queue=self._queue,
            durable=True,
            callback=self._on_queue_declared,
        )

    def _on_queue_declared(self, frame: pika.frame.Method) -> None:
        logger.info("Queue '%s' declared", self._queue)
        self._channel.basic_consume(self._queue, self._dispatch)
        logger.info("Consuming from '%s'", self._queue)

    def _dispatch(
        self,
        channel: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        # try:
        self._on_message(body)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    # except Exception as e:
    #     logger.error("Message handler failed: %s", e)
    #     channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
