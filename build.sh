#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
COLLECTSTATIC_ONLY=1 SECRET_KEY=${SECRET_KEY:-build-only} python manage.py collectstatic --noinput
