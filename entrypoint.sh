#!/bin/sh
python manage.py makemigrations usuarios partidas chat_partida chat_global
python manage.py migrate
python manage.py shell < poblar_bbdd.py

daphne -b 0.0.0.0 -p 8000 sotacaballorey.asgi:application
