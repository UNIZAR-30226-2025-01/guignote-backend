#!/bin/bash

docker stop postgres_container django_container 2>/dev/null
docker rm postgres_container django_container 2>/dev/null

# Inciar contenedores
docker run --name postgres_container -p 5432:5432 -d postgres_image
until docker exec postgres_container pg_isready -U admin -h localhost; do
    sleep 1
done
docker run --name django_container --link postgres_container:db -p 8000:8000 \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=contrasenya \
    -e POSTGRES_DB=Database \
    -e DJANGO_SECRET_KEY="superclave_segura" \
    -e DJANGO_DEBUG="True" \
    -d django_image

echo "Los contenedores están corriendo"
