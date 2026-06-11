release: python manage.py migrate --no-input && python manage.py collectstatic --no-input
web: gunicorn config.wsgi --workers 2 --bind 0.0.0.0:$PORT
