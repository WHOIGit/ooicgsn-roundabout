#!/bin/bash

set -e

# Deletes Items created by the Selenium Webdriver automated tests in linux Docker container. Takes about 14 minutes to run.
echo Running Chrome Tests

node RetireBuilds.js chrome headless admin

node DeleteCruise.js chrome headless admin

node DeleteAssemblies.js chrome headless admin

node DeleteParts.js chrome headless admin

node DeleteLocations.js chrome headless admin

node DeleteUser.js chrome headless admin

exit 0