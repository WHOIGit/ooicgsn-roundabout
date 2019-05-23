#!/bin/bash
# Script to rebuild all Django containers and run migrate/collectstatic to deploy
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

docker-compose -f production-demo-site.yml up -d --no-deps --build django_demo
docker-compose -f production-demo-site.yml run --rm django_demo python manage.py migrate
docker-compose -f production-demo-site.yml run --rm django_demo python manage.py collectstatic --noinput

docker-compose -f production-generic-site.yml up -d --no-deps --build django_generic
docker-compose -f production-generic-site.yml run --rm django_generic python manage.py migrate
docker-compose -f production-generic-site.yml run --rm django_generic python manage.py collectstatic --noinput

docker-compose -f production-rov-site.yml up -d --no-deps --build django_rov
docker-compose -f production-rov-site.yml run --rm django_rov python manage.py migrate
docker-compose -f production-rov-site.yml run --rm django_rov python manage.py collectstatic --noinput

docker-compose -f production.yml up -d --no-deps --build django
docker-compose -f production.yml run --rm django python manage.py migrate
docker-compose -f production.yml run --rm django python manage.py collectstatic --noinput
