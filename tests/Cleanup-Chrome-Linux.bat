#!/bin/bash

set -e

# Deletes Items created by the Selenium Webdriver automated tests in linux Docker container. Takes about 14 minutes to run.
echo Running Chrome Tests


val=$(node RetireBuilds.js chrome headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node DeleteAssemblies.js chrome headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node DeleteParts.js chrome headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

val=$(node DeleteLocations.js chrome headless)
echo $val
if [[ "$val" == *"failed."* ]]; then
  exit 1
fi

exit 0