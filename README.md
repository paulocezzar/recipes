# Recipe Box

Personal recipe app: take a photo of a recipe, Claude reads it into a clean, editable layout, and you can print it or save it as PDF, Word, image or text. Recipes and original photos are kept in Postgres.

## Stack
Django 5.1 · Postgres (own schema) · gunicorn + whitenoise · Anthropic API for photo reading.
The front end is one template (`templates/recipes/app.html`); PDF/Word/image exports are generated in the browser (jsPDF, JSZip, html2canvas from cdnjs).

## Database
All tables live in the Postgres schema named by `DB_SCHEMA` (default `recipebox`). Every connection sets
`search_path=recipebox`, so the app can share the StockUp database without reading or writing StockUp's `public` tables.
`start.sh` creates the schema if it's missing, runs migrations and creates the first login.

## Render settings
| Setting | Value |
|---|---|
| Build command | `./build.sh` |
| Start command | `./start.sh` |
| `SECRET_KEY` | long random string |
| `DATABASE_URL` | **Internal** URL of `bakery-stock-db` |
| `ANTHROPIC_API_KEY` | from console.anthropic.com |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | your first login (created on start-up if it doesn't exist) |
| `ANTHROPIC_MODEL` | optional, default `claude-sonnet-5` |
| `PYTHON_VERSION` | `3.12.7` |

Add more people (e.g. Sandra) at `/admin/` → Users → Add user.

## Local development
```bash
pip install -r requirements.txt
DEBUG=1 SECRET_KEY=dev python manage.py migrate      # SQLite when DATABASE_URL is unset
DEBUG=1 SECRET_KEY=dev ADMIN_USERNAME=me ADMIN_PASSWORD=... python manage.py ensure_admin
DEBUG=1 SECRET_KEY=dev python manage.py runserver
```
