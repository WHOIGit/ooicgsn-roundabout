#!/bin/sh
docker buildx build -f compose/production/django/Dockerfile -t ghcr.io/whoigit/ooicgsn-roundabout:1.7.0 --platform linux/amd64 --push .