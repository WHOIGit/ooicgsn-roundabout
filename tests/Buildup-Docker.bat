#!/bin/bash

set -e

chrome --version
chromedriver -v

# Runs all Roundabout Selenium Webdriver automated tests in linux Docker container to build up the test database.

node AddEditLocations.js chrome headless admin

node AddEditParts.js chrome headless admin 

node AddEditAssemblies.js chrome headless admin 

node AddEditInventory.js chrome headless admin

#node ImportExportInventory.js chrome headless admin

#node ExportCustomFields.js chrome headless admin

node ExportCruise.js chrome headless admin

node AddBuilds.js chrome headless admin 

node ImportExportInventory.js chrome headless admin

node ExportCustomFields.js chrome headless admin

node AdminUser.js chrome headless admin

node ConstantsConfigs.js chrome headless admin

node UploadCsv.js chrome headless admin

node CalibrationsCoefs.js chrome headless admin

node API.js chrome headless admin

exit 0