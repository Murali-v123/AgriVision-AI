#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=================================================="
echo "  AgriVision AI - Render Build Script"
echo "=================================================="

# 1. Upgrade pip and install all project dependencies
echo "==> Step 1/4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Run Django migrations
echo "==> Step 2/4: Applying database migrations..."
python backend/manage.py migrate --noinput

# 3. Seed demonstration accounts (Ramesh Farmer, FreshMart Buyer, Platform Admin)
echo "==> Step 3/4: Seeding demo accounts and initial marketplace data..."
python backend/manage.py seed_demo_data

# 4. Collect static files for WhiteNoise serving
echo "==> Step 4/4: Collecting static assets..."
python backend/manage.py collectstatic --noinput

echo "=================================================="
echo "  AgriVision AI Build Succeeded!"
echo "=================================================="
