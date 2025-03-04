#!/bin/sh
python manage.py makemigrations usuarios
python manage.py makemigrations partidas
python manage.py migrate
gunicorn --bind 0.0.0.0:8000 sotacaballorey.wsgi:application