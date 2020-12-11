rem Runs all Roundabout Selenium Webdriver automated tests in Windows cmd prompt launching Chrome. Takes about 6-11 minutes to run. 
rem Set path to chromedriver.exe
SET PATH=%PATH%;%~dp0\node_modules\chromedriver\lib\chromedriver
cmd /c node AddEditLocations.js chrome > RoundAboutTesting.log 
cmd /c node AddEditParts.js chrome >> RoundAboutTesting.log 
cmd /c node AddEditAssemblies.js chrome >> RoundAboutTesting.log
cmd /c node AddEditInventory.js chrome >> RoundAboutTesting.log
cmd /c node ImportExportInventory.js chrome >> RoundAboutTesting.log
cmd /c node ExportCustomFields.js chrome >> RoundAboutTesting.log
cmd /c node ExportCruise.js chrome >> RoundAboutTesting.log
cmd /c node AddBuilds.js chrome >> RoundAboutTesting.log
cmd /c node RetireBuilds.js chrome >> RoundAboutTesting.log
cmd /c node DeleteCruise.js chrome >> RoundAboutTesting.log
cmd /c node DeleteAssemblies.js chrome >> RoundAboutTesting.log
cmd /c node DeleteParts.js chrome >> RoundAboutTesting.log
cmd /c node DeleteLocations.js chrome >> RoundAboutTesting.log