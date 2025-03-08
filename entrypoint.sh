#!/bin/sh
python sotacaballorey/manage.py makemigrations usuarios
python sotacaballorey/manage.py makemigrations partidas
python sotacaballorey/manage.py makemigrations chat_partida
python sotacaballorey/manage.py migrate
gunicorn --bind 0.0.0.0:8000 sotacaballorey.wsgi:application
