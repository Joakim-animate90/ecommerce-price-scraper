#!/bin/bash
# Superset initialization script

set -e

echo "Initializing Superset..."

# Wait for database
echo "Waiting for database to be ready..."
sleep 10

# Upgrade database
echo "Upgrading Superset database..."
superset db upgrade

# Create admin user if it doesn't exist
echo "Creating admin user..."
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USER:-admin}" \
    --firstname "Admin" \
    --lastname "User" \
    --email "admin@localhost" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || echo "Admin user already exists"

# Initialize Superset
echo "Initializing Superset..."
superset init

echo "Superset initialization complete!"
echo "Access Superset at http://localhost:8088"
echo "Username: ${SUPERSET_ADMIN_USER:-admin}"
echo "Password: ${SUPERSET_ADMIN_PASSWORD:-admin}"
