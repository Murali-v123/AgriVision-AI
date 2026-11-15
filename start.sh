#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=================================================="
echo "  AgriVision AI - Production Server Starting"
echo "=================================================="

# Ensure database migrations are always applied
echo "==> Running database migrations..."
python backend/manage.py migrate --noinput

# Ensure the 3 demo accounts (Farmer, Buyer, Admin) exist on every deploy/restart
echo "==> Ensuring demo accounts exist..."
python backend/manage.py seed_demo_data

# Launch Gunicorn WSGI HTTP Server
echo "==> Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn --chdir backend agrivision.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
