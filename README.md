# Crystal Cook N Serve — Django Website

Full Django website for Crystal Cook N Serve Products Pvt. Ltd. — cookware/kitchenware catalogue with admin dashboard and enquiry system.

## Stack
- Django 6.0 + Jazzmin admin theme
- SQLite (dev) / PostgreSQL (prod via `DATABASE_URL`)
- Gunicorn + WhiteNoise (production)

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
cp .env.example .env     # edit values
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://localhost:8000/` for the site, `/admin/` for the dashboard.

## Project Structure

```
config/        Django settings, urls, wsgi
products/      Brand, Category, Product, Marketplace models
enquiry/       Enquiry + EnquiryItem models
blog/          Blog + BlogCategory models
downloads/     Download model
core/          ContactSubmission model + page views
templates/     All 17 HTML pages
static/        JS, images, admin assets
```

## Deploy on Railway

1. Push this folder to a GitHub repo
2. Create new Railway project → Deploy from GitHub
3. Set environment variables:
   - `SECRET_KEY` (long random string)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=*.up.railway.app`
   - `DATABASE_URL` (auto-injected by Railway Postgres)
4. Railway auto-runs `Procfile`:
   - `release: python manage.py migrate --no-input`
   - `web: gunicorn config.wsgi`
5. After first deploy, open Railway shell:
   ```
   python manage.py createsuperuser
   python manage.py seed_data
   ```
