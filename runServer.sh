#!/bin/bash

# This script will run the Django server on 0.0.0.0:8000, making it accessible externally
echo "Starting Django server on 0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000
