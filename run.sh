#!/bin/bash
docker stop django_container postgres_container redis_container
docker container prune
docker-compose down -v
docker-compose up --build -d
