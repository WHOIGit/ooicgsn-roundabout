rem Runs all Roundabout Selenium Webdriver automated tests in Windows cmd prompt launching Firefox. Takes about 6 - 11 minutes to run. 
rem Set path to geckodriver.exe
SET PATH=%PATH%;%~dp0\node_modules\.bin
start cmd.exe /k "node AddEditLocations.js firefox > RoundAboutTesting.log && node AddEditParts.js firefox >> RoundAboutTesting.log && node AddEditAssemblies.js firefox >> RoundAboutTesting.log && node AddEditInventory.js firefox >> RoundAboutTesting.log && node AddBuilds.js firefox >> RoundAboutTesting.log && node RetireBuilds.js firefox >> RoundAboutTesting.log && node DeleteAssemblies.js firefox >> RoundAboutTesting.log && node DeleteParts.js firefox >> RoundAboutTesting.log && node DeleteLocations.js firefox >> RoundAboutTesting.log"
