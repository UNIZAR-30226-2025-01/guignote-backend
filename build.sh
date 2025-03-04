#!/bin/bash

docker rmi -f postgres_image django_image 2>/dev/null

# Construir imágenes
docker build -t postgres_image -f Dockerfile.postgres .
docker build -t django_image -f Dockerfile.despliegue .

echo "Imágenes construidas"

