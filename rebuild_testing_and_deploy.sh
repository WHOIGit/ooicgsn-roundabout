#!/bin/bash

# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.


# Script to rebuild rdb-testing containers and run migrate/collectstatic to deploy
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

if [ -e production-testing-site.yml ]
then
    docker-compose -f production-testing-site.yml up -d --no-deps --build django_testing
    docker-compose -f production-testing-site.yml run --rm django_testing python manage.py migrate
    docker-compose -f production-testing-site.yml run --rm django_testing python manage.py collectstatic --noinput
    docker-compose -f production-testing-site.yml up -d --no-deps --build celeryworker
    docker-compose -f production-testing-site.yml up -d --no-deps --build celerybeat
    docker-compose -f production-testing-site.yml up -d --no-deps --build flower
fi
