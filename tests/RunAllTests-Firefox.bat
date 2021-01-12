rem Runs all Roundabout Selenium Webdriver automated tests in Windows cmd prompt launching Firefox. Takes about 6 - 11 minutes to run. 
rem Set path to geckodriver.exe
SET PATH=%PATH%;%~dp0\node_modules\.bin
cmd /c node AddEditLocations.js firefox > RoundAboutTesting.log
cmd /c node AddEditParts.js firefox >> RoundAboutTesting.log
cmd /c node AddEditAssemblies.js firefox >> RoundAboutTesting.log
cmd /c node AddEditInventory.js firefox >> RoundAboutTesting.log
cmd /c node ImportExportInventory.js firefox >> RoundAboutTesting.log
cmd /c node ExportCustomFields.js firefox >> RoundAboutTesting.log
cmd /c node AddBuilds.js firefox >> RoundAboutTesting.log
cmd /c node RetireBuilds.js firefox >> RoundAboutTesting.log
cmd /c node DeleteAssemblies.js firefox >> RoundAboutTesting.log
cmd /c node DeleteParts.js firefox >> RoundAboutTesting.log
cmd /c node DeleteLocations.js firefox >> RoundAboutTesting.log
