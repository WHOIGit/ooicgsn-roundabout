#!/bin/sh

# Runs all Roundabout Selenium Webdriver automated tests in linux Docker container. Takes about 11 minutes to run.
node AddEditLocations.js chrome headless && node AddEditParts.js chrome headless  && node AddEditAssemblies.js chrome headless  && node AddEditInventory.js chrome headless  && node AddBuilds.js chrome headless  && node RetireBuilds.js chrome headless  && node DeleteAssemblies.js chrome headless  && node DeleteParts.js chrome headless  && node DeleteLocations.js chrome headless 