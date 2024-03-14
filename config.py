"""
Environment Variables:
- DEALER_URL: URL of the DEALER_URL server.
- MQTT_BROKER_URL: URL of the MQTT broker.
- MQTT_BROKER_PORT: Port of the MQTT broker.
- TOPIC_NAME: MQTT topic to subscribe to for events.
"""

import os


DEALER_URL: str = os.getenv("DEALER_URL", "")
MQTT_BROKER_URL: str = os.getenv("MQTT_BROKER_URL", "mqtt")
MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))

TOPIC_NAME: str = os.getenv("TOPIC_NAME", "")
MEDIA_PATH: str = "media"  # Media path, save converted images from topic
