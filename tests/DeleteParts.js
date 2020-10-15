// JavaScript source code
'use strict';
console.log("Running Delete Parts Test.");

// Generated by Selenium IDE
const { Builder, By, Key, until, a, WebElement, promise, Capabilities } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');

var driver;
var myArgs = process.argv.slice(2);
var user;
var password;

(async function testParts() {

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
        await driver.get("https://ooi-cgrdb-staging.whoi.net/");
        user = "jkoch";
        password = "Automatedtests";
    }

    // 2 | setWindowSize | 1304x834 | 
    await driver.manage().window().setRect({ width: 1304, height: 834 });
    // Set implict wait time in between steps
    await driver.manage().setTimeouts({ implicit: 4000 });

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
        await driver.findElement(By.css(".primaryAction")).click();

        // Delete Part Types, Part Templates and Inventory created running automated tests.

        // 7 | click | id=navbarTemplates | 
        await driver.findElement(By.id("navbarTemplates")).click();
        // 8 | click | linkText=Parts | 
        await driver.findElement(By.linkText("Parts")).click();
        // 9 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 10 | type | id=searchbar-query | Sewing Template
        await driver.findElement(By.id("searchbar-query")).sendKeys("Sewing Template");
        // 11 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 12 | click | linkText=1232 | 
        await new Promise(r => setTimeout(r, 2000));

	if ((await driver.findElements(By.linkText("1232"))).length != 0)
	{
            await driver.findElement(By.linkText("1232")).click();
            // 13 | click | linkText=Delete | 
            await driver.findElement(By.linkText("Delete")).click();
            // 14 | click | css=.btn-danger | 
            await new Promise(r => setTimeout(r, 8000));  //circleci firefox keeps failing here
   	    //let encodedString = await driver.takeScreenshot();
            //await fs.writeFileSync('./sewing.png', encodedString, 'base64');
	    //await driver.navigate().refresh();  //this did not work
            await driver.findElement(By.css(".btn-danger")).click();
	}
	else
	    console.log("Delete Parts failed: Sewing Template not found");

        // 7 | click | id=navbarTemplates | 
        await driver.findElement(By.id("navbarTemplates")).click();
        // 8 | click | linkText=Parts | 
        await driver.findElement(By.linkText("Parts")).click();
        // 9 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 10 | type | id=searchbar-query | Sewing Template
        await driver.findElement(By.id("searchbar-query")).sendKeys("Wheel Template");
        // 11 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 12 | click | linkText=1232 | 
        await new Promise(r => setTimeout(r, 2000));

	if ((await driver.findElements(By.linkText("555-456-789"))).length != 0)
	{
            await driver.findElement(By.linkText("555-456-789")).click();
            // 13 | click | linkText=Delete | 
            await driver.findElement(By.linkText("Delete")).click();
            // 14 | click | css=.btn-danger | 
            await new Promise(r => setTimeout(r, 8000));  //circleci firefox
            await driver.findElement(By.css(".btn-danger")).click();
	}
	else
	    console.log("Delete Parts failed: Wheel Template not found");

	await new Promise(r => setTimeout(r, 4000));  //circleci firefox

        // 7 | click | id=navbarTemplates | 
        await driver.findElement(By.id("navbarTemplates")).click();
        // 8 | click | linkText=Parts | 
        await driver.findElement(By.linkText("Parts")).click();
        // 9 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 10 | type | id=searchbar-query | Sewing Template
        await driver.findElement(By.id("searchbar-query")).sendKeys("Pin Template");
        // 11 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 12 | click | linkText=1232 | 
        await new Promise(r => setTimeout(r, 2000));

	if ((await driver.findElements(By.linkText("666-456-789"))).length != 0)
	{
            await driver.findElement(By.linkText("666-456-789")).click();
            // 13 | click | linkText=Delete | 
            await driver.findElement(By.linkText("Delete")).click();
            // 14 | click | css=.btn-danger | 
            await new Promise(r => setTimeout(r, 8000)); 
            await driver.findElement(By.css(".btn-danger")).click();
	}
	else
	    console.log("Delete Parts failed: Pin Template not found");

        // 7 | click | id=navbarTemplates | 
	await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("navbarTemplates")).click();
        // 8 | click | linkText=Parts | 
        await driver.findElement(By.linkText("Parts")).click();
        // 9 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 10 | type | id=searchbar-query | Sewing Template
        await driver.findElement(By.id("searchbar-query")).sendKeys("Disk Drive");
        // 11 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 12 | click | linkText=1232 | 
        await new Promise(r => setTimeout(r, 2000));

	if ((await driver.findElements(By.linkText("100-259-785"))).length != 0)
	{
            await driver.findElement(By.linkText("100-259-785")).click();
            // 13 | click | linkText=Delete | 
            await driver.findElement(By.linkText("Delete")).click();
            // 14 | click | css=.btn-danger | 
            await new Promise(r => setTimeout(r, 8000)); 
            await driver.findElement(By.css(".btn-danger")).click();
	}
	else
	    console.log("Delete Parts failed: Disk Drive not found");

        // 10 | click | id=navbarTemplates |
        await driver.findElement(By.id("navbarTemplates")).click();
        await driver.findElement(By.id("navbarAdmintools")).click();
        // 5 | click | linkText=Test |
        await driver.findElement(By.linkText("Edit Part Types")).click();


	if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Sewing Machine']"))).length != 0)
	{
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Sewing Machine") {
                    break;
                } 
                i++;
            }
            await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-danger")).click();
            // 6 | click | css=.btn-danger | 
	    await driver.findElement(By.css(".btn-danger")).click();
	}
	else
            console.log("Delete Parts failed: Sewing Machine type not found");

        // Delete Computerized Part Type
        if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Computerized']"))).length != 0) {
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Computerized") {
                    break;
                }
                i++;
            }

	    await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-danger")).click();
            // 6 | click | css=.btn-danger | 
            await driver.findElement(By.css(".btn-danger")).click();
        }
        else
            console.log("Delete Parts failed: Computerized type not found");

	// Delete Custom Fields
        // 10 | click | id=navbarTemplates |
        await driver.findElement(By.id("navbarTemplates")).click();
        await driver.findElement(By.id("navbarAdmintools")).click();
        // 5 | click | linkText=Test |
        await driver.findElement(By.linkText("Custom Fields")).click();


	if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Condition']"))).length != 0)
	{
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Condition") {
                    break;
                } 
                i++;
            }
            await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-danger")).click();
            // 6 | click | css=.btn-danger | 
	    await driver.findElement(By.css(".btn-danger")).click();
	}
	else
            console.log("Delete Parts failed: Condition Custom Field not found");


        // Close browser window
    driver.quit();

    }
    catch (e) {
        console.log(e.message, e.stack);
        console.log("Delete Parts failed.");
	return 1;
    } 

    console.log("Delete Parts completed.")
    return 0;

})();
