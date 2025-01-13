# wsgi.py
import sys
import os

sys.path.insert(0, '/home/runner/work/tunemymood/tunemymood')


from app import create_app

application = create_app()
