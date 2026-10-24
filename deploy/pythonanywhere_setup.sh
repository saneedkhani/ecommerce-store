#!/bin/bash
# One-time (and re-runnable) setup of ShopWave on PythonAnywhere.
#
# In a PythonAnywhere "Bash" console:
#   git clone https://github.com/saneedkhani/ecommerce-store.git ~/ecommerce-store
#   bash ~/ecommerce-store/deploy/pythonanywhere_setup.sh
#
# To update the live site later:
#   cd ~/ecommerce-store && git pull && bash deploy/pythonanywhere_setup.sh
set -e

PROJECT_DIR="$HOME/ecommerce-store"
VENV_DIR="$HOME/.virtualenvs/shopwave"
DOMAIN="${USER}.pythonanywhere.com"
WSGI_FILE="/var/www/${USER}_pythonanywhere_com_wsgi.py"

cd "$PROJECT_DIR"

# Django 6 needs Python 3.12 or newer
PYTHON=""
for candidate in python3.13 python3.12; do
    if command -v "$candidate" > /dev/null; then PYTHON="$candidate"; break; fi
done
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.12+ not found. On the Account page, switch to the newest system image and try again."
    exit 1
fi

echo "==> Virtual environment ($PYTHON)"
[ -d "$VENV_DIR" ] || "$PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "==> Environment file"
if [ ! -f .env ]; then
    SECRET=$(python -c "from django.core.management.utils import get_random_secret_key as k; print(k())")
    cat > .env <<EOF
DJANGO_SECRET_KEY=$SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN
EOF
    echo "    created .env for $DOMAIN (a new secret key was generated)"
else
    echo "    .env already exists, keeping it"
fi

echo "==> Database, static files and demo data"
python manage.py migrate --noinput
python manage.py collectstatic --noinput > /dev/null
python manage.py seed_demo

if [ -f "$WSGI_FILE" ]; then
    echo "==> WSGI file"
    cat > "$WSGI_FILE" <<EOF
# ShopWave WSGI config (written by deploy/pythonanywhere_setup.sh)
import os
import sys

path = '$PROJECT_DIR'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'ecommerce_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF
    touch "$WSGI_FILE"  # reloads the site
    echo "    updated $WSGI_FILE and reloaded the site"
else
    echo "NOTE: $WSGI_FILE not found. Create the web app first (Web tab > Add a new web app > Manual configuration), then run this script again."
fi

cat <<EOF

==> Done! Finish these settings on the Web tab (only needed once):
    Virtualenv:            $VENV_DIR
    Static files:          URL /static/  ->  $PROJECT_DIR/staticfiles
                           URL /media/   ->  $PROJECT_DIR/media
    Security:              turn ON "Force HTTPS"
Then click the green Reload button and open https://$DOMAIN

Create your staff login (choose your own password):
    source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py createsuperuser
EOF
