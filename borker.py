import os
import json
import requests
from typing import Optional, Any, List, Tuple

from PIL import Image
import paho.mqtt.client as mqtt

# Constants for the configuration
FRIGATE_URL = "http://frigate:5000"

def convert_image(byte_data: bytes, event_id: str) -> str:
    """Converts a JPEG image to PNG format and saves it.

    Args:
        byte_data: The binary data of the JPEG image.
        event_id: The unique identifier for the event.

    Returns:
        The path to the converted PNG image or the original JPEG if conversion fails.
    """
    os.makedirs("frigate/state_numbers/", exist_ok=True)
    image_name = f"state_number_{event_id}.jpeg"
    image_path = f"frigate/state_numbers/{image_name}"

    # Write the original JPEG image
    with open(image_path, 'wb') as file:
        file.write(byte_data)

    # Attempt to convert to PNG
    try:
        with Image.open(image_path) as image:
            png_image_path = image_path.replace('.jpeg', '.png')
            image.save(png_image_path, "PNG")
        return png_image_path
    except IOError:
        print(f"Cannot convert image: {image_path}")
        return image_path

def detect_state_number(event_id: str) -> Optional[str]:
    """Detects the state number from an image.

    Args:
        event_id: The unique identifier for the event.

    Returns:
        The detected state number, if any.
    """
    from AutoVision.web.ai_service.app_gts import lp_det_reco  # Importing here to avoid potential circular imports
    image_path = f"frigate/state_numbers/state_number_{event_id}.jpeg"
    attrs = lp_det_reco(image_path)
    return attrs

def send_event(camera_name: str, label: str, boxes: List[Tuple[int, int]], detected_number: str) -> None:
    """Sends an event to a specified URL.

    Args:
        camera_name: The name of the camera that detected the event.
        label: The label for the event.
        boxes: The bounding boxes for the detected objects.
        detected_number: The detected state number.
    """
    full_url_path = f"{FRIGATE_URL}/api/events/{camera_name}/{detected_number}/create"
    data = {
        "sub_label": label,
        "duration": 5,
        "draw": {"boxes": [{"box": boxes, "color": [255, 0, 0], "score": 100}]}
    }

    session = requests.Session()
    session.trust_env = False
    response = session.post(full_url_path, json=data)
    print(response.content)

def get_event_data(event_id: str) -> Optional[bytes]:
    """Fetches event data.

    Args:
        event_id: The unique identifier for the event.

    Returns:
        The binary content of the event data or None if not found.
    """
    full_url_path = f"{FRIGATE_URL}/api/events/{event_id}/snapshot.jpg"
    session = requests.Session()
    session.trust_env = False
    response = session.get(full_url_path)
    if response.content:
        return response.content
    return None

def on_connect(client: mqtt.Client, userdata: Any, flags: dict, rc: int, properties: Optional[dict] = None) -> None:
    """Callback for when the client receives a CONNACK response from the server."""
    print(f"Connected with result code {rc}")
    client.subscribe("frigate/events/#")

def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    """Callback for when a PUBLISH message is received from the server."""
    topic_data = json.loads(msg.payload)
    event_id = topic_data["before"].get("id")
    box = topic_data["after"].get("box")
    camera = topic_data["before"].get("camera")
    byte_data = get_event_data(event_id)
    if byte_data:
        convert_image(byte_data, event_id)
        detected_number_result = detect_state_number(event_id)
        if detected_number_result:
            detected_number = detected_number_result[0]  # Assuming function returns a list
            send_event(camera_name=camera, label="state_number", boxes=box, detected_number=detected_number)
    else:
        print("Failed request to service")

# MQTT Client setup
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

# Connect to the MQTT broker
mqttc.connect("mqtt", 1883, 60)
