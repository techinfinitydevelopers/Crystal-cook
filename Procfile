release: python manage.py migrate --no-input && python manage.py loaddata wp_products
web: gunicorn config.wsgi --workers 2 --bind 0.0.0.0:$PORT
