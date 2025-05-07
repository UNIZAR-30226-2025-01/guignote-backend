#!/bin/bash

#Script empleado para limpiar la memoria innecesaria ocupada pro las pruebas de docker

docker rmi $(docker images --filter "dangling=true" -q --no-trunc)
docker volume prune
