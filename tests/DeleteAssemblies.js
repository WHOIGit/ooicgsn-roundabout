// JavaScript source code
'use strict';
console.log('Running Delete Assemblies Test');

// Generated by Selenium IDE
const { Builder, By, Key, until, a, WebElement, promise } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const assert = require('assert');
const chromedriver = require('chromedriver');
const { exception } = require('console');

var driver;

(async function deleteAssemblies() {

    driver = new Builder().forBrowser('chrome').build();

    // Step # | name | target | value
    // 1 | open | https://ooi-cgrdb-staging.whoi.net/ | 
    await driver.get("https://ooi-cgrdb-staging.whoi.net/");
    // 2 | setWindowSize | 1304x834 | 
    await driver.manage().window().setRect(1304, 834);

    try {

        // LOGIN
        await driver.findElement(By.linkText("Sign In")).click();
        await driver.findElement(By.id("id_login")).sendKeys("jkoch");
        await driver.findElement(By.id("id_password")).sendKeys("Automatedtests");
        await driver.findElement(By.css(".primaryAction")).click();

        // DELETE ASSEMBLIES TEST

       // Searches for and deletes the Assemblies added during the Add and Update Assemblies Test

        await driver.findElement(By.xpath("//button[contains(.,'Search')]")).click();
        await driver.findElement(By.id("search-model-dropdown")).click();
        await driver.findElement(By.linkText("Assembly Templates")).click();
        // 3 | removeSelection | id=field-select_c_r0 | label=Number
 //       await driver.findElement(By.id("field-select_c_r0")).click();
        {
            const dropdown = await driver.findElement(By.id("field-select_c_r0"));
            await dropdown.findElement(By.xpath("//option[. = 'Name']")).click();
        }
 
        // 6 | click | id=qfield-lookup_c_r0 | 
        await driver.findElement(By.id("qfield-lookup_c_r0")).click();
        // 7 | select | id=qfield-lookup_c_r0 | label=Exact
        {
            const dropdown = await driver.findElement(By.id("qfield-lookup_c_r0"));
            await dropdown.findElement(By.xpath("//option[. = 'Exact']")).click();
        }
 
        // 10 | type | id=field-query_c_r0 | Test Assembly
        await driver.findElement(By.id("field-query_c_r0")).sendKeys("Test Assembly");
        // 11 | click | id=searchform-submit-button | 
        await driver.findElement(By.id("searchform-submit-button")).click();
        // 12 | click | linkText=123-001 | 
        await driver.findElement(By.linkText("123-001")).click();
        // 13 | click | linkText=Delete | 
        await driver.findElement(By.linkText("Delete")).click();
        // 14 | click | css=.btn-danger | 
        await driver.wait(until.elementLocated(By.css(".btn-danger")));
        await driver.findElement(By.css(".btn-danger")).click();

        // 15 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 16 | type | id=searchbar-query | Test Assembly 2
        await driver.findElement(By.id("searchbar-query")).sendKeys("Test Assembly 2");
        // 17 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 18 | click | linkText=123-002 | 
        await driver.findElement(By.linkText("123-002")).click();
        // 22 | click | linkText=Delete | 
        await driver.findElement(By.linkText("Delete")).click();
        // 23 | click | css=.btn-danger | 
        await driver.wait(until.elementLocated(By.css(".btn-danger")));
        await driver.findElement(By.css(".btn-danger")).click();

        // 24 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 25 | type | id=searchbar-query | Test Assembly 3
        await driver.findElement(By.id("searchbar-query")).sendKeys("Test Assembly 3");
        // 26 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 27 | click | linkText=123-003 | 
        await driver.findElement(By.linkText("123-003")).click();
        // 28 | click | linkText=Delete | 
        await driver.findElement(By.linkText("Delete")).click();
        // 29 | click | css=.btn-danger | 
        await driver.wait(until.elementLocated(By.css(".btn-danger")));
        await driver.findElement(By.css(".btn-danger")).click();

        // 30 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        // 31 | type | id=searchbar-query | Test Glider 1
        await driver.findElement(By.id("searchbar-query")).sendKeys("Test Glider 1");
        // 32 | click | css=.btn-outline-primary:nth-child(1) | 
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();
        // 33 | click | linkText=000-654-987 | 
        await driver.findElement(By.linkText("000-654-987")).click();
        // 34 | click | linkText=Delete | 
        await driver.findElement(By.linkText("Delete")).click();
        // 35 | click | css=.btn-danger | 
        await driver.wait(until.elementLocated(By.css(".btn-danger")));
        await driver.findElement(By.css(".btn-danger")).click();

    }
    catch (e) {
        console.log(e.message, e.stack);
        console.log("Delete Assemblies failed.");
        throw (e);
    } 

    console.log("Delete Assemblies completed.")
    return;

})();