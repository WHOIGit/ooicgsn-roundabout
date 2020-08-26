#!/bin/bash

set -e

# Runs all Roundabout Selenium Webdriver automated tests in linux Docker container. Takes about 11 minutes to run.
echo Run Firefox Tests

val=$(node AddEditLocations.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node AddEditParts.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node AddEditAssemblies.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node AddEditInventory.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node AddBuilds.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node RetireBuilds.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node DeleteAssemblies.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node DeleteParts.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node DeleteLocations.js firefox headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

exit 0