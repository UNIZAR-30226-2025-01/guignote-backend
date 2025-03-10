#! /bin/bash

./build.sh
./run.sh
docker exec -it django_container /bin/bash
