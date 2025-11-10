web: gunicorn core.wsgi:application
worker: celery -A core worker --loglevel=info
beat: celery -A core beat --loglevel=info
flower: celery -A core flower --port=5555 --broker="redis://default:OblhjneUIMOGnKPPjyrvueAPVgWOoOxe@shuttle.proxy.rlwy.net:51367" --address=0.0.0.0
