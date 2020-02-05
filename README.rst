Roundabout DB - OOI Parts and Inventory Web Application
=========================================================

Current Version: 1.0

Django application to manage Part, Location, and Deployment Templates, and Inventory tracking for OOI Electrical Engineering. Uses PostgreSQL database.


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
Deployment
============

Production
----------

Prerequisites
^^^^^^^^^^^^^

To deploy a production instance of Roundabout, you need to have the following items in place:

- A web server with ports 80 and 443 available
- Docker and docker-compose installed on the server (`<https://docs.docker.com/compose/install/>`_)
- Git installed on the server

Environmental Variables
^^^^^^^^^^^^^^^^^^^^^^^
Roundabout relies heavily on environmental variables. The environmental variables include secrets like database usernames/passwords.
These variable should NOT be kept in version control. The repository includes a ".envs.example" directory that you can use as
a template to create your own ".envs" directory. Roundabout requires this ".envs" directory to be in the application root level directory.


Local Docker Development
^^^^^^^^^^^^^^^^^^^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html
