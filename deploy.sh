#!/bin/bash

# Navigate to the application directory


# Activate the virtual environment
source /home/bdnsysif/virtualenv/bdnsys.com/nazri_bdn/tena/3.11/bin/activate && cd /home/bdnsysif/bdnsys.com/nazri_bdn/tena
# Install any new dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart the application to apply changes
# This depends on your cPanel host's method; often done by touching the passenger_wsgi.py file.
touch tmp/restart.txt