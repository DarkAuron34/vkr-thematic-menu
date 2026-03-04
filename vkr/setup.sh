#!/bin/bash
python -m venv .venv
python -m pip install Django Pillow
# python -m pip install django-crispy-forms
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
