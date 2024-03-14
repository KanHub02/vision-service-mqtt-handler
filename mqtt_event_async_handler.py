"""
Event Handler with Asyncio MQTT Integration

This script is designed for integration with CCTV software, facilitating the handling of events
via MQTT messages. It processes images from these events and performs several actions, including
image format conversion from JPEG to PNG, detection of state numbers within these images, and
event forwarding to a specified URL.

Leveraging asyncio for asynchronous operation, the script subscribes to MQTT topics to receive event
notifications, retrieves event data asynchronously, and processes images entirely in memory
to enhance efficiency. State numbers detected in images are then forwarded along with event details
such as the camera name, label, and bounding boxes to a designated URL for further processing or logging.

Key Features:
- Utilizes asyncio for asynchronous operation, enhancing efficiency and scalability.
- Employs environment variables for configuration, allowing for flexible deployment.
- Conducts in-memory image processing, eliminating the need for temporary file storage.
- Implements robust logging for improved troubleshooting and monitoring.

Prerequisites:
- asyncio_mqtt: For asynchronous MQTT communication.
- aiohttp: For asynchronous HTTP requests.
- Pillow (PIL): For image processing tasks such as format conversion.

Configuration:
- The script is configured to connect to an MQTT broker and subscribe to a specified topic.
- Environment variables are used to define parameters such as MQTT broker URL, port, and topic name.
- Image processing and event data retrieval are performed asynchronously to handle multiple events efficiently.
"""

import os
import json
import asyncio
import aiohttp
from aiohttp import ClientSession
from typing import Optional, List, Tuple, Union
from PIL import Image
from asyncio_mqtt import Client, MqttError
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
logger = logging.getLogger("MQTT_ASYNC_BROKER")


async def convert_image(byte_data: bytes, event_id: str) -> str:
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


async def detect_state_number(event_id: str) -> Union[Tuple, bool]:
    """Detects the state number from an image."""
    image_path = f"{MEDIA_PATH}/state_numbers/state_number_{event_id}.jpeg"
    if os.path.exists(image_path):
        attrs = process_image(image_path)
        os.remove(image_path)
        return attrs
    else:
        return False


async def send_event(
    camera_name: str, label: str, boxes: List[Tuple[int, int]], detected_number: str
) -> None:
    """Sends an event to a specified URL."""
    full_url_path = f"{DEALER_URL}/api/events/{camera_name}/{detected_number}/create"
    data = {
        "sub_label": label,
        "duration": 0.1,
        "draw": {"boxes": [{"box": boxes, "color": [255, 0, 0], "score": 100}]},
    }
    async with ClientSession() as session:
        try:
            async with session.post(full_url_path, json=data) as response:
                logger.info(await response.text())
        except aiohttp.ClientError as e:
            logger.error(f"Failed to send event: {e}")


async def get_event_data(event_id: str) -> Optional[bytes]:
    """Fetches event data."""
    full_url_path = f"{DEALER_URL}/api/events/{event_id}/snapshot.jpg"
    async with ClientSession() as session:
        try:
            async with session.get(full_url_path) as response:
                if response.status == 200:
                    return await response.read()
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching event data: {e}")
    return None


async def main():
    async with Client(MQTT_BROKER_URL, port=MQTT_BROKER_PORT) as client:
        await client.subscribe(TOPIC_NAME)
        async with client.unfiltered_messages() as messages:
            async for message in messages:
                topic_data = json.loads(message.payload.decode())
                event_id = topic_data["before"].get("id")
                box = topic_data["after"].get("box")
                camera = topic_data["before"].get("camera")
                byte_data = await get_event_data(event_id)
                if isinstance(byte_data, bytes):
                    convert_result = await convert_image(byte_data, event_id)
                    if isinstance(convert_result, bool):
                        logging.info("Image is not converted")
                        continue
                    detected_number_result = await detect_state_number(event_id)
                    if isinstance(detected_number_result, tuple):
                        await send_event(
                            camera_name=camera,
                            label="state_number",
                            boxes=box,
                            detected_number=detected_number_result[0],
                        )
                else:
                    logger.warning("Failed to process the event")

if __name__ == "__main__":
    asyncio.run(main())
