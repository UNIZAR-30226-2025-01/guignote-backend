#! /bin/bash
./run.sh
docker exec -it django_container ./test.sh
