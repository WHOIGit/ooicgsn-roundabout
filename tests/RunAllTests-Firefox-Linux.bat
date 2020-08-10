#!/bin/sh

# Runs all Roundabout Selenium Webdriver automated tests in linux Docker container. Takes about 11 minutes to run.
node AddEditLocations.js firefox headless  && node AddEditParts.js firefox headless  && node AddEditAssemblies.js firefox headless  && node AddEditInventory.js firefox headless  && node AddBuilds.js firefox headless  && node RetireBuilds.js firefox headless  && node DeleteAssemblies.js firefox headless  && node DeleteParts.js firefox headless  && node DeleteLocations.js firefox headless 