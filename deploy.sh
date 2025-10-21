#!/bin/bash

# Navigate to the application directory


# Activate the virtual environment
source /home/oce295lv5izw/virtualenv/public_html/dansileshi.org/bdn_ftp/home/oce295lv5izw/public_html/bdn_ftp/danipage/3.11/bin/activate && cd /home/oce295lv5izw/public_html/dansileshi.org/bdn_ftp/home/oce295lv5izw/public_html/bdn_ftp/danipage
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