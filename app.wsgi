import sys
import logging
sys.path.insert(0, '/var/www/nerc')
sys.path.insert(0, '/var/www/nerc/vocprez')
logging.basicConfig(stream=sys.stderr)

from app import app as application
