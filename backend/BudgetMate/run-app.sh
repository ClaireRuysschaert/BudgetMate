#!/bin/bash

set -ex

if [ ! -z "$APP_EXEC_MODE_RUNSERVER" ]; then
    rm -rf static
    python manage.py collectstatic --noinput --settings=BudgetMate.settings.development
    python manage.py migrate --settings=BudgetMate.settings.development
    echo "Create Superuser"
    python manage.py createsu --settings=BudgetMate.settings.development --force-reset-password
    echo "Run App"
    exec python manage.py runserver --settings=BudgetMate.settings.development 0.0.0.0:8000
elif [ ! -z "$DJANGO_SETTINGS_MODULE" ]; then
    python manage.py collectstatic --noinput --settings=$DJANGO_SETTINGS_MODULE
    python manage.py migrate --settings=$DJANGO_SETTINGS_MODULE
    if [ ! -z "$DJANGO_CREATE_SU_OPTIONS" ]; then
      python manage.py createsu --settings=$DJANGO_SETTINGS_MODULE $DJANGO_CREATE_SU_OPTIONS
    fi
    exec python run_logged_gunicorn_app.py
else
    python manage.py collectstatic --noinput --settings=BudgetMate.settings.production
    python manage.py migrate --settings=BudgetMate.settings.production
    python manage.py createsu --settings=BudgetMate.settings.production $DJANGO_CREATE_SU_OPTIONS
    exec python run_logged_gunicorn_app.py
fi
