web: gunicorn core.wsgi:application
worker: celery -A core worker --loglevel=info --concurrency=2 --pool=prefork --broker="redis://default:OblhjneUIMOGnKPPjyrvueAPVgWOoOxe@shuttle.proxy.rlwy.net:51367"
