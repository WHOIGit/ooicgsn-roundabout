// JavaScript source code
'use strict';
console.log("Running Delete Locations Test.");

// Generated by Selenium IDE
const { Builder, By, Key, until, a, WebElement, promise, Capabilities} = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');
const assert = require('assert');

var driver;
var myArgs = process.argv.slice(2);
var user;
var password;

(async function deleteLocations() {

    let chromeCapabilities = Capabilities.chrome();
    var firefoxOptions = new firefox.Options();

    // Docker linux chrome will only run headless
    if ((myArgs[1] == 'headless') && (myArgs.length !=0)) {
    
	 chromeCapabilities.set("goog:chromeOptions", {
      	   args: [
      	    "--no-sandbox",
       	    "--disable-dev-shm-usage",
       	    "--headless",
	    "--log-level=3",
	    "--disable-gpu"
     	    ]
   	    });

	  firefoxOptions.addArguments("-headless");
    } 

    // First argument specifies the Browser type
    if (myArgs[0] == 'chrome') {        
        driver = new Builder().forBrowser('chrome').withCapabilities(chromeCapabilities).build();
    }
    else if (myArgs[0] == 'firefox') {       
        driver = new Builder().forBrowser('firefox').setFirefoxOptions(firefoxOptions).build();
    } 
    else {
	console.log('Error: Missing Arguments');
    }

   if (myArgs[2] == 'admin')
    {
        await driver.get("http://localhost:8000/");
        user = "admin";
        password = "admin";
    }
    else
    {
//        await driver.get("https://ooi-cgrdb-staging.whoi.net/");
        await driver.get("https://rdb-testing.whoi.edu/");
        user = "jkoch";
        password = "Automatedtests";
    }

    // 2 | setWindowSize | 1304x834 | 
    await driver.manage().window().setRect({ width: 1304, height: 834 });
    // Set implict wait time in between steps//
//    await driver.manage().setTimeouts({ implicit: 2000 });

    //Hide Timer Panel when connecting to circleci local rdb django app
    if ((await driver.findElements(By.css("#djHideToolBarButton"))).length != 0)
    {
       await driver.findElement(By.css("#djHideToolBarButton")).click();
    }

    try {

        // If navbar toggler present in small screen
        try {
            var signin = await driver.findElement(By.linkText("Sign In"));
        }
        catch (NoSuchElementException) {
                await driver.findElement(By.css(".navbar-toggler-icon")).click();
         }
        // LOGIN
        await driver.findElement(By.linkText("Sign In")).click();
        await driver.findElement(By.id("id_login")).sendKeys(user);
        await driver.findElement(By.id("id_password")).sendKeys(password);
        await driver.findElement(By.css(".primaryAction")).click()

        // DELETE LOCATIONS TEST

        // Delete location with no children
        // 10 | click | id=navbarTemplates |
        await driver.findElement(By.id("navbarTemplates")).click();
        // 11 | click | linkText=Locations | 
        await driver.findElement(By.linkText("Locations")).click(); 
        // 5 | click | linkText=Test | 
        await new Promise(r => setTimeout(r, 2000));

	if ((await driver.findElements(By.linkText("Test1"))).length != 0)
	{
            await driver.findElement(By.linkText("Test1")).click(); 
            // 6 | click | linkText=Delete | 
//	    await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.linkText("Delete"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete1.");
	    }
            await driver.findElement(By.linkText("Delete")).click();
//            await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.css(".btn-danger"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete1.");
	    }
            // 7 | click | css=.btn-danger | 
            await driver.findElement(By.css(".btn-danger")).click();
            await new Promise(r => setTimeout(r, 6000));
	}
	else
	    console.log("Delete Locations failed: Test1 not found");

        // Expand all first level tree nodes   
        var j = 1;
        while (true) {
            try {
               await new Promise(r => setTimeout(r, 2000));
                await driver.findElement(By.xpath("//div/ul/li[" + j + "]/i")).click();
         }
        catch (e) {
            break;
        }
        j++;
        }
        
	if ((await driver.findElements(By.linkText("Test Child1"))).length != 0)
	{
	    await driver.findElement(By.linkText("Test Child1")).click();
//            await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.linkText("Delete"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete2.");
	    }
            // 9 | click | linkText=Delete | 
            await driver.findElement(By.linkText("Delete")).click();
//	    await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.css(".btn-danger"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete2.");
	    }
            // 10 | click | css=.btn-danger | 
            await driver.findElement(By.css(".btn-danger")).click();
	    await new Promise(r => setTimeout(r, 6000));
	}
	else
	    console.log("Delete Locations failed: Test Child1 not found");

        // 18 | click | linkText=Test Child |
	if ((await driver.findElements(By.linkText("Test Child"))).length != 0)
	{
            await driver.findElement(By.linkText("Test Child")).click();
            // 19 | click | linkText=Delete | 
//            await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.linkText("Delete"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete3.");
	    }
            await driver.findElement(By.linkText("Delete")).click();
//	    await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.css(".btn-danger"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete3.");
	    }
            // 20 | click | css=.btn-danger | 
            await driver.findElement(By.css(".btn-danger")).click();
            await new Promise(r => setTimeout(r, 6000));
	}
	else
	    console.log("Delete Locations failed: Test Child not found");

	if ((await driver.findElements(By.linkText("Test"))).length != 0)
	{   
            await driver.findElement(By.linkText("Test")).click();
//            await new Promise(r => setTimeout(r, 8000)); //6 seconds not enough 1.6
	    while ((await driver.findElements(By.linkText("Delete"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete4.");
	    }
            // 25 | click | linkText=Delete | 
            await driver.findElement( By.linkText("Delete")).click();
//            await new Promise(r => setTimeout(r, 6000));
	    while ((await driver.findElements(By.css(".btn-danger"))).length == 0) // 1.6
	    {
	      await new Promise(r => setTimeout(r, 2000));
	      console.log("Wait 2 seconds for Delete4.");
	    }
            // 26 | click | css=.btn-danger | 
            await driver.findElement(By.css(".btn-danger")).click();
            await new Promise(r => setTimeout(r, 6000));
	}
	else
	    console.log("Delete Locations failed: Test not found");

        // Close browser window
        driver.quit();

    }
    catch (e) {
        console.log(e.message, e.stack);
        console.log("Delete Locations failed.");
	return 1;
    }
    console.log("Delete Locations completed.");
    return 0;

})();