"""MQTT client for sbot remote communication."""
from __future__ import annotations

import atexit
import json
import logging
import os
import time
from threading import Event
from typing import Any, Callable, TypedDict
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

LOGGER = logging.getLogger(__name__)

# check if we have the variables we need
MQTT_VALID = 'SBOT_MQTT_URL' in os.environ


class MQTTClient:
    """
    Wrapper around the Paho MQTT client.

    Runs the client in a background thread and handles subscriptions and
    message callbacks.
    """

    def __init__(
        self,
        client_name: str | None = None,
        topic_prefix: str | None = None,
        mqtt_version: mqtt.MQTTProtocolVersion = mqtt.MQTTProtocolVersion.MQTTv5,
        use_tls: bool | str = False,
        username: str = '',
        password: str = '',
    ) -> None:
        self.subscriptions: dict[
            str, Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None]
        ] = {}
        self.topic_prefix = topic_prefix
        self._client_name = client_name
        self._img_topic = 'img'

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_name,
            protocol=mqtt_version,
        )
        self._client.on_connect = self._on_connect

        if use_tls:
            self._client.tls_set()
            if use_tls == 'insecure':
                self._client.tls_insecure_set(True)

        if username:
            self._client.username_pw_set(username, password)

    def connect(self, host: str, port: int) -> None:
        """
        Connect to the MQTT broker and start event loop in background thread.

        Registers an atexit routine that tears down the client.
        """
        if self._client.is_connected():
            LOGGER.error("Attempting connection, but client is already connected.")
            return

        try:
            self._client.connect_async(host, port, keepalive=60)
        except ValueError:
            LOGGER.error(f"Failed to connect to MQTT broker at {host}:{port}")
            return
        self._client.loop_start()
        atexit.unregister(self.disconnect)  # Avoid duplicate atexit handlers
        atexit.register(self.disconnect)

    @classmethod
    def establish(
        cls, host: str, port: int, **kwargs: Any,
    ) -> 'MQTTClient':
        """Create client and connect."""
        client = cls(**kwargs)
        client.connect(host, port)
        return client

    def disconnect(self) -> None:
        """Disconnect from the broker and close background event loop."""
        self._client.disconnect()
        self._client.loop_stop()
        atexit.unregister(self.disconnect)

    def subscribe(
        self,
        topic: str,
        callback: Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None],
        abs_path: bool = False,
    ) -> None:
        """Subscribe to a topic and assign a callback for messages."""
        if not abs_path and self.topic_prefix is not None:
            full_topic = f"{self.topic_prefix}/{topic}"
        else:
            full_topic = topic

        self.subscriptions[full_topic] = callback
        self._subscribe(full_topic, callback)

    def _subscribe(
        self,
        topic: str,
        callback: Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None],
    ) -> None:
        LOGGER.debug(f"Subscribing to {topic}")
        self._client.message_callback_add(topic, callback)
        self._client.subscribe(topic, qos=1)

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        try:
            del self.subscriptions[topic]
        except KeyError:
            pass
        self._client.message_callback_remove(topic)
        self._client.unsubscribe(topic)

    def publish(
        self,
        topic: str,
        payload: bytes | str,
        retain: bool = False,
        *,
        abs_topic: bool = False,
    ) -> None:
        """Publish a message to the broker."""
        if not self._client.is_connected():
            LOGGER.debug(
                "Attempted to publish message, but client is not connected.",
            )
            return

        if not abs_topic and self.topic_prefix:
            topic = f"{self.topic_prefix}/{topic}"

        try:
            self._client.publish(topic, payload=payload, retain=retain, qos=1)
        except ValueError as e:
            raise ValueError(f"Cannot publish to MQTT topic: {topic}") from e

    def wrapped_publish(
        self,
        topic: str,
        payload: bytes | str,
        retain: bool = False,
        *,
        abs_topic: bool = False,
    ) -> None:
        """Wrap a payload up to be decodable as JSON."""
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')

        payload_dict = {
            "timestamp": time.time(),
            "data": payload,
        }

        if 'run_uuid' in os.environ:
            payload_dict['run_uuid'] = os.environ['run_uuid']

        self.publish(
            topic,
            json.dumps(payload_dict),
            retain=retain, abs_topic=abs_topic)

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        connect_flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if reason_code.is_failure:
            LOGGER.warning(
                f"Failed to connect to MQTT broker. Return code: {reason_code.getName()}"  # type: ignore[no-untyped-call]
            )
            return

        LOGGER.debug("Connected to MQTT broker.")

        for topic, callback in self.subscriptions.items():
            self._subscribe(topic, callback)


class MQTTVariables(TypedDict):
    """Variables for connecting to an MQTT broker."""

    host: str
    port: int
    topic_prefix: str
    use_tls: bool | str
    username: str | None
    password: str | None


def get_mqtt_variables() -> MQTTVariables:
    """Get MQTT variables from environment variables."""
    if not MQTT_VALID:
        raise ValueError("MQTT variables are not set.")

    # url format: mqtt[s]://<username>:<password>@<host>:<port>/<topic_root>
    mqtt_url = os.environ['SBOT_MQTT_URL']

    url_parts = urlparse(mqtt_url, allow_fragments=False)
    use_tls = (url_parts.scheme == 'mqtts')

    if url_parts.hostname is None:
        raise ValueError("MQTT URL is missing a hostname.")

    return MQTTVariables(
        host=url_parts.hostname,
        port=url_parts.port or (8883 if use_tls else 1883),
        topic_prefix=url_parts.path.lstrip('/'),
        use_tls=use_tls,
        username=url_parts.username,
        password=url_parts.password,
    )


class RemoteStartButton:
    """MQTT client for the remote start button."""

    def __init__(self, mqtt_client: MQTTClient) -> None:
        self._mqtt_client = mqtt_client
        self._start_pressed = Event()

        self._mqtt_client.subscribe('start_button', self._process_start_message)

    def _process_start_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        try:
            payload = json.loads(message.payload)
        except json.JSONDecodeError:
            LOGGER.warning("Failed to decode start button message.")
            return
        else:
            if 'pressed' in payload.keys():
                if payload['pressed']:
                    self._start_pressed.set()
                    LOGGER.debug("Start button pressed.")
                else:
                    self._start_pressed.clear()
                    LOGGER.debug("Start button cleared.")

    def get_start_button_pressed(self) -> bool:
        """Get the start button pressed status."""
        pressed = self._start_pressed.is_set()
        self._start_pressed.clear()
        return pressed
