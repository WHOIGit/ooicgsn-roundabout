// JavaScript source code
'use strict';
console.log("Running Export Custom Fields Test.");

// Generated by Selenium IDE
const { Builder, By, Key, until, a, WebElement, promise, Capabilities } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');
const assert = require('assert');
const { exception } = require('console');

var driver;
var myArgs = process.argv.slice(2);
var user;
var password;

(async function exportCustomFields() {

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
    // Step # | name | target | value
    if (myArgs[1] == 'headless')
    {
        await driver.get("http://localhost:8000/");   
        user = "admin";
        password = "admin";
    }
    else
    {
        // 1 | open | https://ooi-cgrdb-staging.whoi.net/ | 
        await driver.get("https://ooi-cgrdb-staging.whoi.net/");
        user = "jkoch";
        password = "Automatedtests";
    }

    // 2 | setWindowSize | 1304x834 | 
    await driver.manage().window().setRect({ width: 1304, height: 834 });

    //Hide Timer Panel when connecting to circleci local rdb django app
    if ((await driver.findElements(By.css("#djHideToolBarButton"))).length != 0)
    {
       await driver.findElement(By.css("#djHideToolBarButton")).click();
       await new Promise(r => setTimeout(r, 4000));
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

        // EXPORT CUSTOM FIELDS TEST

        // Uncheck all Global Part Types for the Custom Field

        // 10 | click | id=navbarAdminTools |
        await driver.findElement(By.id("navbarAdmintools")).click();
         // 4 | click | linkText=Custom Fields | 
        await driver.findElement(By.linkText("Custom Fields")).click();
        if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Condition']"))).length != 0) {
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Condition") {
                    break;
                }
                i++;
            }
            await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-primary")).click();
        }
        else
            console.log("Export Custom Fields failed: Condition Custom Field not found");

 
        var i = 1;
        while (true) {
            try {
                var clicked = await driver.findElement(By.xpath("//div[" + i + "]/label/input")).isSelected();
                if (clicked)
                {
                    await driver.findElement(By.xpath("//div[" + i + "]/label/input")).click();
                }
            }
            catch (e) {
                break;
            }
            i++;
        }
        // 18 | click | css=.btn-primary | 
        await driver.findElement(By.css(".btn-primary")).click();

        // Create Computerized Part Template
        // 13 | click | id=navbarTemplates | 
        await driver.findElement(By.id("navbarTemplates")).click();
        // 14 | click | linkText=Parts | 
        await driver.wait(until.elementLocated(By.linkText("Parts")));
        await driver.findElement(By.linkText("Parts")).click();
        // 15 | click | linkText=Add Part Template | 
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Add Part Template")).click();
        /*Get the text after ajax call*/
        // 16 | type | id=id_part_number |
        var part_num = "100-259-785";
        await driver.wait(until.elementLocated(By.id("id_part_number")));
        await driver.findElement(By.id("id_part_number")).sendKeys(part_num);
        // 17 | type | id=id_name | Computerized
        await driver.findElement(By.id("id_name")).sendKeys("Disk Drive");
        // 18 | type | id=id_friendly_name | sewing
        await driver.findElement(By.id("id_friendly_name")).sendKeys("drive");
        // 19 | select | id=id_part_type | label=Computerized
        {
            var dropdown = await driver.findElement(By.id("id_part_type"));
            await dropdown.findElement(By.xpath("//option[. = ' Computerized']")).click();

        }
        // 20 | click | css=.controls > .btn | 
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));

        var obj = await driver.findElements(By.xpath("//*[text()='Part with this Part number already exists.']"));
        if (obj.length != 0) {
            throw new Error("Please run the Delete Parts Test. Computerized Template already created");
        }

        // Create Inventory with Part Template above
        await driver.findElement(By.linkText("Inventory")).click();
        await new Promise(r => setTimeout(r, 4000)); // Inventory tree takes awhile to load
        // 4 | click | linkText=Add Inventory | 
        await driver.wait(until.elementLocated(By.linkText("Add Inventory")));
        await driver.findElement(By.linkText("Add Inventory")).click();
        await driver.wait(until.elementLocated(By.id("id_part_type")));
        // 5 | select | id=id_part_type | label=-- Sewing Machine
        {
            const dropdown = await driver.findElement(By.id("id_part_type"));
            await dropdown.findElement(By.xpath("//option[. = '-- Computerized']")).click();
        }
        // 6 | select | id=id_part | label=Disk Drive
        {
            await new Promise(r => setTimeout(r, 2000));
            const dropdown = await driver.findElement(By.id("id_part"));
            await dropdown.findElement(By.xpath("//option[. = 'Disk Drive']")).click();
        }
        // 7 | select | id=id_location | label=Test
        {
            const dropdown = await driver.findElement(By.id("id_location"));
            // There's a space before Test in the option dropdown
            await dropdown.findElement(By.xpath("//option[. = ' Test']")).click();
        }
        // 8 | storeValue | id=id_serial_number | Serial_Number
        // Stores the value of the Serial Number assigned
        await new Promise(r => setTimeout(r, 2000));
        var Serial_Number = await driver.findElement(By.id("id_serial_number")).getAttribute("value");
        // 10 | click | css=.controls > .btn | 
        await driver.findElement(By.css(".controls > .btn")).click();
       
        // Now, check all Global Types for the Custom Field

        // 10 | click | id=navbarAdminTools |
        await driver.findElement(By.id("navbarAdmintools")).click();
        // 4 | click | linkText=Custom Fields | 
        await driver.findElement(By.linkText("Custom Fields")).click();
        if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Condition']"))).length != 0) {
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Condition") {
                    break;
                }
                i++;
            }
            await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-primary")).click();
        }
        else
            console.log("Export Custom Fields failed: Condition Custom Field not found");


        var i = 1;
        while (true) {
            try {
                var clicked = await driver.findElement(By.xpath("//div[" + i + "]/label/input")).isSelected();
                if (!clicked) {
                    await driver.findElement(By.xpath("//div[" + i + "]/label/input")).click();
                }
            }
            catch (e) {
                break;
            }
            i++;
        }
        // 18 | click | css=.btn-primary | 
        await driver.findElement(By.css(".btn-primary")).click();

        // Search for and Export Part Items and verify "Condition" Custom Field is exported
        // 3 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        await driver.findElement(By.id("searchbar-modelselect")).click()
        // 8 | select | id=searchbar-modelselect | label=Part Templates
        {
            const dropdown = await driver.findElement(By.id("searchbar-modelselect"))
            await dropdown.findElement(By.xpath("//option[. = 'Part Templates']")).click()
        }
        // 5 | click | css=.btn:nth-child(1) | 
        await driver.findElement(By.css(".btn:nth-child(1)")).click()

        // Downloads to Downloads Folder
        // 10 | click | id=search--download-csv-button |
        await driver.findElement(By.id("search--download-csv-button")).click();
        // 11 | click | linkText=All (Include Hidden Columns) | 
        await driver.findElement(By.linkText("All (Include Hidden Columns)")).click();

        // Read RDB_Part.csv and verify Condition Custom Field
        var fs = require('fs');
        const jsdom = require("jsdom");
        const { JSDOM } = jsdom;
        const { window } = new JSDOM(`...`);
        var $ = require('jquery')(window);
        $.csv = require('jquery-csv');
        var data;

	    if (myArgs[1] == 'headless')
	    {
	    	var rdb_inv = process.cwd()+"//RDB_Part.csv";
	    }
	    else
	    {
           const execSync = require('child_process').execSync;
            var username = execSync('echo %username%', { encoding: 'utf-8' });
            username = username.replace(/[\n\r]+/g, '');
            var rdb_inv = "C:\\Users\\" + username + "\\Downloads\\RDB_Part.csv";
        } 
     	
        // Read in the exported Part Template csv data  
        await new Promise(r => setTimeout(r, 40000));  //Wait for file to be created
        var csv = fs.readFileSync(rdb_inv, 'utf8');
        var exported_data = $.csv.toArrays(csv);
        for (var i = 0, len = exported_data[0].length; i < len; i++) {
            if (exported_data[0][i] == "Part Number")
            {
                var epart_num_index = i;
            }
            if (exported_data[0][i] == "Condition (Default)")
            {
                var econdition_index = i;
            }
        } 

        var condition = "Good";
        var part_num_found = false;
        // Check if Part Num and Custom Field in exported data matches created Part Template.
        //Find the created part number and verify condition matches
        for (var j = 1, elen = exported_data.length; j < elen; j++) {
            if (part_num == exported_data[j][epart_num_index])
            {
                if (condition == exported_data[j][econdition_index]) {
                    console.log("Condition Custom Field matches for Part Template: ", part_num, ".");
                }
                else {
                    throw new error("Condition Custom Field does not match for Part Number: " + part_num + ".");
                }
                part_num_found = true;
            }
        }
        if (!part_num_found)
        {
            throw new error(part_num+" not found.");
        }

        // Search for and Export Inventory Items
        // 3 | click | id=searchbar-query | 
        await driver.findElement(By.id("searchbar-query")).click();
        await driver.findElement(By.id("searchbar-modelselect")).click()
        // 8 | select | id=searchbar-modelselect | label=Part Templates
        {
            const dropdown = await driver.findElement(By.id("searchbar-modelselect"))
            await dropdown.findElement(By.xpath("//option[. = 'Inventory']")).click()
        }
        // Search for Disk Drive - export all inventory fails 
        await driver.findElement(By.id("searchbar-query")).sendKeys("Disk Drive");
        // 5 | click | css=.btn:nth-child(1) | 
        await driver.findElement(By.css(".btn:nth-child(1)")).click()

        // Downloads to Downloads Folder
        // 10 | click | id=search--download-csv-button |
        await driver.findElement(By.id("search--download-csv-button")).click();
        // 11 | click | linkText=All (Include Hidden Columns) | 
        await driver.findElement(By.linkText("All (Include Hidden Columns)")).click();

        if (myArgs[1] == 'headless') {
            var rdb_inv = process.cwd() + "//RDB_Inventory.csv";
        }
        else {
            const execSync = require('child_process').execSync;
            var username = execSync('echo %username%', { encoding: 'utf-8' });
            username = username.replace(/[\n\r]+/g, '');
            var rdb_inv = "C:\\Users\\" + username + "\\Downloads\\RDB_Inventory.csv";
        }

        // Read in the exported Part Template csv data  
        await new Promise(r => setTimeout(r, 40000));  //Wait for file to be created
        var csv = fs.readFileSync(rdb_inv, 'utf8');
        var exported_data = $.csv.toArrays(csv);

        for (var i = 0, len = exported_data[0].length; i < len; i++) {
            if (exported_data[0][i] == "Serial Number") {
                var eserial_num_index = i;
            }
            if (exported_data[0][i] == "Condition") {
                var econdition_index = i;
            }
        } 

        // Check if Serial Number and Custom Field in exported data matches created Assembly.
        //Find the created serial number and verify condition matches
        var serial_num_found = false;
        for (var j = 1, elen = exported_data.length; j < elen; j++) {
            if (Serial_Number == exported_data[j][eserial_num_index]) {
                if (condition == exported_data[j][econdition_index])
                {
                    console.log("Condition Custom Field matches for Inventory:", Serial_Number, ".");
                }
                else {
                    throw new error("Condition Custom Field does not match for Inventory:" + Serial_Number + ".");
                }
                serial_num_found = true;
            }
        }
        if (!serial_num_found) {
            throw new error(Serial_Number + " not found.");
        }
	    
        // Close browser window
        driver.quit();

    }
    catch (e) {
        console.log(e.message, e.stack);
        console.log("Export Custom Fields failed.");
	return 1;
    } 

    console.log("Export Custom Fields completed.")
    return 0;

})();