Overview

The Async MQTT CCTV Event Processor project is designed to integrate with CCTV systems, handling events through MQTT messages. It processes images from these events for custom actions such as image format conversion, state number detection, and forwarding events to a specified URL. This solution utilizes asynchronous operations to enhance efficiency and scalability, making it ideal for real-time event processing in surveillance applications.
Features

    Asynchronous Operation: Leverages asyncio and asyncio_mqtt for non-blocking event handling.
    Image Processing: Converts JPEG images to PNG in memory and detects state numbers without the need for temporary storage.
    Event Forwarding: Sends detected events, along with camera metadata and processed images, to a designated endpoint.
    Robust Configuration: Uses environment variables and supports Docker-based deployment for ease of use and flexibility.

Prerequisites

    Docker and Docker Compose
    Git

Getting Started
Clone the Repository

First, clone the repository and its submodules using the following command:

bash

git clone --recurse-submodules git@github.com:PetaBytePro/vision_service.git

This command clones the main repository and initializes and updates each submodule in the repository, such as the vision_service submodule.
Setup with Docker

The project includes a docker-compose.yml file that defines the setup for running the service. To get everything up and running:

    Build and Run the Service:

    Navigate to the project directory and run:

    bash

    docker-compose up --build

    This command builds the Docker image and starts the service as defined in docker-compose.yml. It installs necessary dependencies and starts the mqtt_event_handler.py script in an environment configured according to the project's requirements.

Configuration

Configuration is managed through environment variables and the config.py file. Make sure to set the following environment variables according to your setup:

    MQTT_BROKER_URL: The URL of the MQTT broker.
    MQTT_BROKER_PORT: The port on which the MQTT broker is running.
    TOPIC_NAME: The MQTT topic to subscribe to for receiving events.
    DEALER_URL: The URL to which detected events should be forwarded.
    MEDIA_PATH: The path where media files should be stored or processed.

Vision Service Submodule

This project uses the vision_service as a submodule, which provides image processing capabilities required for state number detection and other image-related processing tasks. Ensure that the submodule is correctly initialized and updated within your project clone.
Usage

Once deployed, the service automatically subscribes to the specified MQTT topic, listens for incoming messages, and processes them as per the script's logic. Processed data, including image conversions and detected information, is then forwarded to the configured URL for further handling or logging.
Contributing

Contributions to the Async MQTT CCTV Event Processor project are welcome. Please ensure to follow the project's code style guidelines and submit your pull requests for review.
