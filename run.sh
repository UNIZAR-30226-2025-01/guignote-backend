#!/bin/bash

# Stop the running containers
docker stop django_container postgres_container redis_container

# Remove all stopped containers
docker container prune -f

# Take down the docker-compose setup, including volumes (-v option)
docker-compose down -v

# Rebuild and start the containers in detached mode
docker-compose up --build -d

# Wait for the database to be ready before running the Django command
echo "Waiting for the database to be ready..."
until docker exec -it postgres_container pg_isready -U postgres; do
  sleep 2
done

# Run Django's loaddata command to load initial data
echo "Loading initial data..."
docker exec -it django_container python manage.py loaddata --verbosity 2 --app aspecto_carta initial_data.json
docker exec -it django_container python manage.py loaddata --verbosity 2 --app tapete initial_data.json


