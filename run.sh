#!/bin/bash

docker stop postgres_container django_container redis_container 2>/dev/null
docker rm postgres_container django_container redis_container 2>/dev/null

# Iniciar contenedor PostgreSQL
docker run --name postgres_container -p 5432:5432 -d postgres_image
until docker exec postgres_container pg_isready -U admin -h localhost; do
    sleep 1
done

# Inciar contenedor de Redis
docker run --name redis_container -p 6379:6379 -d redis:alpine

# Iniciar contenedor de Django
docker run --name django_container --link postgres_container:db --link redis_container:redis -p 8000:8000 \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=contrasenya \
    -e POSTGRES_DB=Database \
    -e DJANGO_SECRET_KEY="superclave_segura" \
    -e DJANGO_DEBUG="True" \
    -e REDIS_HOST=redis_container \
    -e REDIS_PORT=6379 \
    -e DJANGO_SETTINGS_MODULE="sotacaballorey.settings" \
    -d django_image

echo "Los contenedores están corriendo"
