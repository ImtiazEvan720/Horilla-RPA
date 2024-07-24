#!/bin/bash

# Define your variables
DJANGO_SETTINGS_MODULE="myproject.settings"
DJANGO_APP="horilla"

# Navigate to the project directory (assuming the script is run from the root)
cd "$(dirname "$0")" || exit

# Activate the virtual environment (located one level above)
source ../venv/bin/activate  # Adjust if necessary

# Wait for the database to be ready
echo "Waiting for database to be ready..."
sleep 10  # Adjust as necessary for your database readiness check

# Apply migrations
echo "Applying migrations..."
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# Check if the user exists and create if not
if ! python3 manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(username='admin').exists())"; then
    echo "Creating admin user..."
    python3 manage.py createhorillauser --first_name admin --last_name admin --username admin --password admin --email admin@example.com --phone 1234567890
else
    echo "Admin user already exists."
fi

# Start the Gunicorn server
echo "Starting the Gunicorn server..."
gunicorn --bind 0.0.0.0:80 horilla.wsgi:application &

# Start the Celery worker
echo "Starting the Celery worker..."
celery -A $DJANGO_APP worker --loglevel=info &
celery -A $DJANGO_APP beat --loglevel=debug

