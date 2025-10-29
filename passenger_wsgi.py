import os
import sys





from django.core.wsgi import get_wsgi_application
sys.path.append('/bdnsys.com/nazri_bdn/tena/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenabot.settings')
application = get_wsgi_application()

#from danipage.wsgi import application

