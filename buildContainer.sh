!#/bin/bash

#!/bin/bash

# Define image name
IMAGE_NAME="ginyote-base"

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

echo "Build complete!"

