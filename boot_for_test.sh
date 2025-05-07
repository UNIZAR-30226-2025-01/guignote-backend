#!/bin/bash
cd "$(dirname "$0")"
./run.sh
docker exec -it django_container /bin/bash
