#!/usr/bin/env bash
set -o errexit
# Runs on every start: create the app's own schema, migrate it, make the first login.
python manage.py ensure_schema
python manage.py migrate --noinput
python manage.py ensure_admin
exec gunicorn recipebox.wsgi:application --bind 0.0.0.0:${PORT:-10000} --timeout 120 --workers 1 --threads 4 --worker-class gthread
