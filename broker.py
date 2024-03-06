"""
Frigate Event Handler with MQTT Integration

This script is designed to integrate with the Frigate CCTV software, handling events
via MQTT messages, processing images from those events, and performing custom actions
such as image format conversion, state number detection, and event forwarding to a specified URL.

The script uses MQTT to subscribe to Frigate events, retrieves event data, converts
JPEG images to PNG in memory (without the need for temporary storage), and detects state
numbers from these images using a placeholder function. Detected events are then sent
to a specified URL with the camera name, label, bounding boxes, and detected state number.

Key Features:
- Utilizes environment variables for easy configuration.
- Implements in-memory image processing for efficiency.
- Includes robust logging for easier troubleshooting and monitoring.

Environment Variables:
- FRIGATE_URL: URL of the Frigate server.
- MQTT_BROKER_URL: URL of the MQTT broker.
- MQTT_BROKER_PORT: Port of the MQTT broker.
- TOPIC_NAME: MQTT topic to subscribe to for Frigate events.

Prerequisites:
- paho-mqtt: For MQTT communication.
- Pillow (PIL): For image processing.
- requests: For HTTP requests to send events.

Author: Your Name
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
"""

import os
import json
import requests
from typing import Optional, List, Tuple
from PIL import Image
import paho.mqtt.client as mqtt
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEALER_URL = os.getenv("DEALER_URL", "")
MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL", "")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC_NAME = os.getenv("TOPIC_NAME", "frigate/events/#")


def convert_image_in_memory(byte_data: bytes) -> bytes:
    """Converts a JPEG image bytes to PNG format bytes."""
    try:
        with Image.open(io.BytesIO(byte_data)) as image:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
    except IOError as e:
        logger.error(f"Error converting image: {e}")
        return byte_data


def detect_state_number(image_bytes: bytes) -> Optional[str]:
    """Detects the state number from image bytes."""
    pass


def send_event(
    camera_name: str, label: str, boxes: List[Tuple[int, int]], detected_number: str
) -> None:
    """Sends an event to a specified URL."""
    full_url_path = f"{DEALER_URL}/api/events/{camera_name}/{detected_number}/create"
    data = {
        "sub_label": label,
        "duration": 5,
        "draw": {"boxes": [{"box": boxes, "color": [255, 0, 0], "score": 100}]},
    }
    try:
        response = requests.post(full_url_path, json=data)
        logger.info(response.content)
    except requests.RequestException as e:
        logger.error(f"Failed to send event: {e}")


def get_event_data(event_id: str) -> Optional[bytes]:
    """Fetches event data."""
    full_url_path = f"{DEALER_URL}/api/events/{event_id}/snapshot.jpg"
    try:
        response = requests.get(full_url_path)
        if response.content:
            return response.content
    except requests.RequestException as e:
        logger.error(f"Error fetching event data: {e}")
    return None


def on_connect(client, userdata, flags, rc, properties=None):
    logger.info(f"Connected with result code {rc}")
    client.subscribe(TOPIC_NAME)


def on_message(client, userdata, msg):
    topic_data = json.loads(msg.payload)
    event_id = topic_data["before"].get("id")
    box = topic_data["after"].get("box")
    camera = topic_data["before"].get("camera")
    byte_data = get_event_data(event_id)
    if byte_data:
        png_data = convert_image_in_memory(byte_data)
        detected_number_result = detect_state_number(png_data)
        if detected_number_result:
            send_event(
                camera_name=camera,
                label="state_number",
                boxes=box,
                detected_number=detected_number_result,
            )
    else:
        logger.warning("Failed to process the event")


mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)
