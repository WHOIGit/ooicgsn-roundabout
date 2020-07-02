// JavaScript source code
'use strict';
console.log('Running Add Builds Test');

// Generated by Selenium IDE
const { Builder, By, Key, until, a, WebElement, promise } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const assert = require('assert');

var driver;
var myArgs = process.argv.slice(2);

(async function addBuilds() {

    // First argument specifies the Browser type, chrome is default if no argument is supplied
    if ((myArgs[0] == 'chrome') || (myArgs.length == 0)) {        
        driver = new Builder().forBrowser('chrome').build();
    }
    else {
        driver = new Builder().forBrowser('firefox').build();
    }

    // Step # | name | target | value
    // 1 | open | https://ooi-cgrdb-staging.whoi.net/ | 
    await driver.get("https://ooi-cgrdb-staging.whoi.net/");
    // 2 | setWindowSize | 1304x834 | 
    await driver.manage().window().setRect(1304, 834);
    // Set implict wait time in between steps
    await driver.manage().setTimeouts({ implicit: 2000 });

    try {

        // LOGIN
        await driver.findElement(By.linkText("Sign In")).click();
        await driver.findElement(By.id("id_login")).sendKeys("jkoch");
        await driver.findElement(By.id("id_password")).sendKeys("Automatedtests");
        await driver.findElement(By.css(".primaryAction")).click();

        // ADD BUILDS TEST

        // Add build with non null assembly template, build number, and location
        await driver.findElement(By.linkText("Builds")).click();
        // 4 | click | linkText=Create New Build | 
        await driver.wait(until.elementLocated(By.linkText("Create New Build")));
        await driver.findElement(By.linkText("Create New Build")).click();
        await new Promise(r => setTimeout(r, 2000));  //needed for firefox build number to populate
        // 5 | select | id=id_assembly | label=Test Glider 1
        {
            const dropdown = await driver.findElement(By.id("id_assembly"));
            await dropdown.findElement(By.xpath("//option[. = 'Test Glider 1']")).click();
        }
        await new Promise(r => setTimeout(r, 2000));  //needed for firefox build number to populate

        // 6 | select | id=id_location | label=--- Test Child
        {
            const dropdown = await driver.findElement(By.id("id_location"));
            await dropdown.findElement(By.xpath("//option[. = '--- Test Child']")).click();
        }
        // 7 | type | id=id_build_notes | This is an automated test build.
        await driver.findElement(By.id("id_build_notes")).sendKeys("This is an automated test build.");
        // 8 | click | css=.controls > .btn | 
        await driver.findElement(By.css(".controls > .btn")).click();
        // 9 | click | linkText=Create New Build | 

        // Verify Build is created in Test Child Location
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click(); // search button
        // 20 | click | id=field-select_c_r0 | 
        await driver.wait(until.elementLocated(By.id("field-select_c_r0")));
        await driver.findElement(By.id("field-select_c_r0")).click();
        // 21 | select | id=field-select_c_r0 | label=Location
        {
            const dropdown = await driver.findElement(By.id("field-select_c_r0"));
            await dropdown.findElement(By.xpath("//option[. = 'Location']")).click();
        }
        // 22 | select | id=qfield-lookup_c_r0 | label=Exact
        {
            const dropdown = await driver.findElement(By.id("qfield-lookup_c_r0"));
            await dropdown.findElement(By.xpath("//option[. = 'Exact']")).click();
        }
        // 23 | type | id=field-query_c_r0 | Lost
        await driver.findElement(By.id("field-query_c_r0")).sendKeys("Test Child");
        // 24 | click | id=searchform-submit-button | 
        await driver.findElement(By.id("searchform-submit-button")).click();
        // 25 | click | css=.even a | 
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.xpath("//p[contains(.,'1 items match your search!')]"));

        // Add build with null assembly template, assembly revision, build number or location
        await driver.findElement(By.linkText("Builds")).click();
        await driver.wait(until.elementLocated(By.linkText("Create New Build")));
        await driver.findElement(By.linkText("Create New Build")).click();
        // 10 | select | id=id_assembly | label=Test Glider 1
        {
            const dropdown = await driver.findElement(By.id("id_assembly"));
            await dropdown.findElement(By.xpath("//option[. = 'Test Glider 1']")).click();
        }
        // 11 | click | css=.controls > .btn | 
        await driver.findElement(By.css(".controls > .btn")).click()
        // 12 | verifyText | css=.ajax-error | This field is required.
        assert(await driver.findElement(By.css("#div_id_location .ajax-error")).getText() == "This field is required.");
        // 13 | select | id=id_location | label=Test
        {
            const dropdown = await driver.findElement(By.id("id_location"));
            // Space required before Test
            await dropdown.findElement(By.xpath("//option[. = ' Test']")).click();
        }
        // 14 | select | id=id_assembly | label=---------
        {
            const dropdown = await driver.findElement(By.id("id_assembly"))
            await dropdown.findElement(By.xpath("//option[. = '---------']")).click();
        }
        // 15 | click | css=.controls > .btn | 
        await driver.findElement(By.css(".controls > .btn")).click();
        // 16 | verifyText | css=.ajax-error | This field is required.
        assert(await driver.findElement(By.css("#div_id_assembly .ajax-error")).getText() == "This field is required.");
        // 17 | select | id=id_assembly | label=Test Glider 1
        {
            const dropdown = await driver.findElement(By.id("id_assembly"));
            await dropdown.findElement(By.xpath("//option[. = 'Test Glider 1']")).click();
        }
        // 18 | type | id=id_build_number |  
        await driver.findElement(By.id("hint_id_build_number")).click();
        await driver.findElement(By.id("id_build_number")).clear();
        // 19 | click | css=.controls > .btn | 
        await driver.findElement(By.css(".controls > .btn")).click();
        // 20 | verifyText | css=.ajax-error | This field is required.
        assert(await driver.findElement(By.css("#div_id_build_number .ajax-error")).getText() == "This field is required.");

    }
    catch (e) {
        console.log(e.message, e.stack);
        console.log("Add Builds failed.");
        throw (e);
    }
    console.log("Add Builds completed.")


})();
