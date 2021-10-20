# Roundabout DB - OOI Parts and Inventory Web Application

Django application to manage Part, Location, and Assembly Templates, and Inventory tracking for OOI-CGSN arrays. Uses PostgreSQL database.

[![License: GPL v2 or later](https://img.shields.io/badge/License-GPL%20v2+-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

## Requirements

## Django 3.1

- Based on [Django Cookiecutter](http://cookiecutter-django.readthedocs.io/en/latest/index.html) template and included apps
- django-mptt - Django app to use Modified Preorder Tree Traversal for hierarchical data models
- django-model-utils - Field Tracker utility
- django-allauth - Registration/Authorization
- django-crispy-forms - Forms

## JS/CSS

- jQuery 3.3.1
- jsTree 3.3
- Bootstrap 4

## Production Deployment

Detailed deployment instructions in the [Wiki](https://github.com/WHOIGit/ooicgsn-roundabout/wiki/RBD---Installation)

## Local Docker Development

See detailed [cookiecutter-django Docker documentation] (http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).
