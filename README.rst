Roundabout DB - OOI Parts and Inventory Web Application
=========================================================

Current Version: 1.0.3

Django application to manage Part, Location, and Assembly Templates, and Inventory tracking for OOI-CGSN arrays. Uses PostgreSQL database.


:License: GPL v3


============
Requirements
============

Django 2.2
------------------
- Based on Django Cookiecutter template and included apps (http://cookiecutter-django.readthedocs.io/en/latest/index.html)
- django-mptt - Django app to use Modified Preorder Tree Traversal for hierarchical data models
- django-model-utils - Field Tracker utility
- django-allauth - Registration/Authorization
- django-crispy-forms - Forms

JS/CSS
------
- jQuery 3.3.1
- jsTree 3.3
- Bootstrap 4

============
Production Deployment
============

Prerequisites
-------------

To deploy a production instance of Roundabout, you need to have the following items in place:

- A web server with ports 80 and 443 available
- Docker and Docker Compose installed on the server (`<https://docs.docker.com/compose/install/>`_)
- Git installed on the server

Environmental Variables
^^^^^^^^^^^^^^^^^^^^^^^
Roundabout relies heavily on environmental variables. The environmental variables include secrets like database usernames/passwords.
These variable should NOT be kept in version control. The repository includes a ``.envs.example`` directory that you can use as
a template to create your own ``.envs`` directory. **Roundabout requires this ".envs" directory to be in the application root level directory**.

The environmental variables include several standard required Django settings that you should update to your own values, including:

- DJANGO_SECRET_KEY
- DJANGO_ALLOWED_HOSTS
- POSTGRES_HOST
- POSTGRES_PORT
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD

In addition to standard Django variables, Roundabout uses some custom environmental variables to set the pattern for the auto-generation of Serial Numbers. There are several options available for you to choose from in the ``.env/production/django`` file:

1) If you want to enable basic Serial Number auto-generation, set the ``RDB_SERIALNUMBER_CREATE`` variable to ``True``. This will create Serial Numbers with a basic numeric pattern - "1, 2, 3, ... etc."
2) If you want to use the Serial Number pattern recommended by OOI, then also set the ``RDB_SERIALNUMBER_OOI_DEFAULT_PATTERN`` variable to ``True``. This will create Serial Numbers with the following pattern: "Part Number" + "-20001, -20002, -20003, etc."

NGINX Settings
^^^^^^^^^^^^^^

The Docker production deployment uses a NGINX container as a web server and proxy to the Django app. An example NGINX conf file (``nginx-example.conf.EXAMPLE``) is included in the ``/compose/production/nginx/`` directory that you can use as a template for HTTP or HTTPS deployment. 

If using SSL, you also need to upload your SSL certificates to the the application root level directory in a new ``/.ssl/certs/`` directory.  These will be copied into the NGINX container when Docker builds the containers.  This directory should also NOT be kept in version control. If you're not using SSL (you should really use SSL), comment out the following line in the production.yml file and update the NGINX conf file accordingly:

.. code:: YAML

    volumes:
      - production_nginx:/var/log/nginx
      - ./.ssl/certs:/etc/ssl/certs/ # bind a local directory with the SSL certs <-- REMOVE THIS LINE

Deployment Steps
----------------

1) Clone the repository to whatever directory on your server you want to use.
2) Upload your NEW ``.envs`` directory and ``.ssl`` directory (if using) to the application root directory.
3) Run the following Docker Compose commands:

.. code:: console

    docker-compose -f production.yml build
    docker-compose -f production.yml up -d
    
4) You're done! Site should be availabe at whatever domain you specified in NGINX.
 
Using Roundabout for the First Time
--------------------------------
 
Not that your site is up and running, you can login by clicking the "Sign In" link and using the default user credentials created when the site was spun up for the first time. These credentials are set in the ``.env/production/django`` file, and - unless you changed them before starting the site -- default to:
 
- Username: admin
- Password: admin
 
You should update these immediately after logging in the first time by clicking the "My Profile" link.
 
Alfresco
---------
 
The standard Roundabout production deployment also includes a standalone Alfresco document management application running in separate Docker containers. You can access Alfresco at https://YOURDOMAIN.com/share/
 
Initial login info is:
 
- Username: admin
- Password: admin
 
If you don't have the need for a document management system running alongside your RDB site, you can simply remove the four Alfresco container Services in the ``production.yml`` Docker Compose file - ``alfresco``, ``alfresco-share``, ``alfresco-postgres``, and ``alfresco-solr6`` - and the three Volumes defined in the ``volumes`` section - ``alfresco-repo-data``, ``alfresco-postgres-data``, ``alfresco-solr-data``.

Local Docker Development
^^^^^^^^^^^^^^^^^^^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html
