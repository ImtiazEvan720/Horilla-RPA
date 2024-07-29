#!/bin/bash

# Define your variables
DJANGO_SETTINGS_MODULE="myproject.settings"
DJANGO_APP="horilla"

echo "Waiting for database to be ready..."
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createhorillauser --first_name admin --last_name admin --username admin --password admin --email admin@example.com --phone 1234567890
gunicorn --bind 0.0.0.0:80 horilla.wsgi:application &
# Start the Celery worker
echo "Starting the Celery worker..."
celery -A $DJANGO_APP worker --loglevel=info &
celery -A $DJANGO_APP beat --loglevel=debug