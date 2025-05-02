#! /bin/bash


SCRIPT_DIR=$(dirname "$(realpath "$0")")
cd "$SCRIPT_DIR"

./build.sh
./run.sh
docker exec -it django_container /bin/bash
