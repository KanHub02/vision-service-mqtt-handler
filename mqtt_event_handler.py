"""
Event Handler with MQTT Integration

This script is designed to integrate with the CCTV software, handling events
via MQTT messages, processing images from those events, and performing custom actions
such as image format conversion, state number detection, and event forwarding to a specified URL.

The script uses MQTT to subscribe to events, retrieves event data, converts
JPEG images to PNG in memory (without the need for temporary storage), and detects state
numbers from these images using a placeholder function. Detected events are then sent
to a specified URL with the camera name, label, bounding boxes, and detected state number.

Key Features:
- Utilizes environment variables for easy configuration.
- Implements in-memory image processing for efficiency.
- Includes robust logging for easier troubleshooting and monitoring.

Prerequisites:
- paho-mqtt: For MQTT communication.
- Pillow (PIL): For image processing.
- requests: For HTTP requests to send events.
"""

import os
import json
import requests
from typing import Optional, List, Tuple, Union
from PIL import Image
import paho.mqtt.client as mqtt
import logging

from vision_service.execute import process_image
from config import (
    DEALER_URL,
    MQTT_BROKER_URL,
    MQTT_BROKER_PORT,
    TOPIC_NAME,
    MEDIA_PATH,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MQTT_BROKER")


def convert_image(byte_data: bytes, event_id: str) -> str:
    """Converts a JPEG image to PNG format and saves it.

    Args:
        byte_data: The binary data of the JPEG image.
        event_id: The unique identifier for the event.

    Returns:
        The path to the converted PNG image or the original JPEG if conversion fails.
    """
    os.makedirs(f"{MEDIA_PATH}/state_numbers/", exist_ok=True)
    image_name = f"state_number_{event_id}.jpeg"
    image_path = f"{MEDIA_PATH}/state_numbers/{image_name}"

    # Write the original JPEG image
    with open(image_path, "wb") as file:
        file.write(byte_data)

    # Attempt to convert to PNG
    try:
        with Image.open(image_path) as image:
            png_image_path = image_path.replace(".jpeg", ".png")
            image.save(png_image_path, "PNG")
        return png_image_path
    except IOError:
        logger.error(f"Cannot convert image: {image_path}")
        os.remove(image_path)
        return False


def detect_state_number(event_id: str) -> Union[Tuple, bool]:
    """Detects the state number from an image.

    Args:
        event_id: The unique identifier for the event.

    Returns:
        The detected state number, if any.
    """
    image_path = f"{MEDIA_PATH}/state_numbers/state_number_{event_id}.jpeg"
    if os.path.exists(image_path):
        attrs = process_image(image_path)
        os.remove(image_path)
        return attrs

    else:
        return False


def send_event(
    camera_name: str, label: str, boxes: List[Tuple[int, int]], detected_number: str
) -> None:
    """Sends an event to a specified URL."""
    full_url_path = f"{DEALER_URL}/api/events/{camera_name}/{detected_number}/create"
    data = {
        "sub_label": label,
        "duration": 0.1,
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
    if isinstance(byte_data, bytes):
        convert_result = convert_image(byte_data, event_id)
        if isinstance(convert_result, bool):
            logging.info("Image is not converted")
            return
        detected_number_result = detect_state_number(event_id)
        if isinstance(detected_number_result, tuple):
            send_event(
                camera_name=camera,
                label="state_number",
                boxes=box,
                detected_number=detected_number_result[0],
            )
    else:
        logger.warning("Failed to process the event")


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)
mqttc.loop_forever()
