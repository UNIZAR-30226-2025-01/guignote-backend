#!/bin/bash

# Define container and image names
CONTAINER_NAME="base-container"
IMAGE_NAME="ginyote-base"
DB_PORT="5433"

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Run the new container
echo "Starting new container: $CONTAINER_NAME..."
docker run -d --name $CONTAINER_NAME -p $DB_PORT:5432 $IMAGE_NAME

echo "Container $CONTAINER_NAME is running!"
