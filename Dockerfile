# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the dependencies file to the working directory
COPY vision_service/requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies
RUN apt-get update && apt-get install -y wget ffmpeg libsm6 libxext6 && \
    wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb && \
    dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb && \
    rm libssl1.1_1.1.0g-2ubuntu4_amd64.deb

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Change the working directory to /usr/src/app/vision_service before running setup.py
WORKDIR /usr/src/app/vision_service
RUN python3 setup.py -q develop
