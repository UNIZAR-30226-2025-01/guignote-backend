#!/bin/sh
python manage.py makemigrations usuarios
python manage.py makemigrations partidas
python manage.py makemigrations chat_partida
pythin manage.py makemigrations chat_global
python manage.py migrate
python manage.py shell < poblar_bbdd.py

gunicorn --bind 0.0.0.0:8000 sotacaballorey.wsgi:application
