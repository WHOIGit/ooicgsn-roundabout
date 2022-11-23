// JavaScript source code
'use strict';
console.log("Running Add & Edit Parts Test.");

// Generated by Selenium IDE
const { Builder, By, Key, until, a, WebElement, promise, Capabilities } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');
const assert = require('assert');
const fs = require('fs');

var driver;
var dropdown;
var myArgs = process.argv.slice(2);
var user;
var password;

(async function testParts() {

    let chromeCapabilities = Capabilities.chrome();
    var firefoxOptions = new firefox.Options();

    // Docker linux chrome will only run headless
    if ((myArgs[1] == 'headless') && (myArgs.length != 0)) {

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

    if (myArgs[2] == 'admin') {
        await driver.get("http://localhost:8000/");
        user = "admin";
        password = "admin";
    }
    else {
        //        await driver.get("https://ooi-cgrdb-staging.whoi.net/");
        await driver.get("https://rdb-testing.whoi.edu/");
        user = "jkoch";
        password = "Automatedtests";
    }

    await driver.manage().window().setRect({ width: 1304, height: 834 });
    // Set implict wait time in between steps
    // await driver.manage().setTimeouts({ implicit: 2000 }); //AddEditPart fails with implicit wait

    //Hide Timer Panel
    if ((await driver.findElements(By.css("#djHideToolBarButton"))).length != 0) {
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

        // ADD PARTS TEST

        console.log("Add Parts running...");

        // Create a Custom Fields Manufacturer and Model, required for sensor_vocab.csv bulk upload
        await driver.findElement(By.id("navbarAdmintools")).click();
        await driver.findElement(By.linkText("Custom Fields")).click();
        while ((await driver.findElements(By.linkText("Add Custom Field"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Custom Field.");
        }
        await driver.findElement(By.linkText("Add Custom Field")).click();
        while ((await driver.findElements(By.id("id_field_name"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Custom Field1.");
        }
        await driver.findElement(By.id("id_field_name")).click();
        await driver.findElement(By.id("id_field_name")).sendKeys("Manufacturer");
        await driver.findElement(By.id("id_field_description")).click();
        await driver.findElement(By.id("id_field_description")).sendKeys("Required for ADCPS-J");
        await driver.findElement(By.id("id_field_type")).click();
        {
            const dropdown = await driver.findElement(By.id("id_field_type"));
            await dropdown.findElement(By.xpath("//option[. = 'Text Field']")).click();
        }

        await driver.findElement(By.id("id_field_default_value")).sendKeys("Teledyne RDI");
        await driver.findElement(By.id("id_global_for_part_types_4")).click();  //instruments
        await driver.findElement(By.css(".btn-primary")).click();

        while ((await driver.findElements(By.linkText("Add Custom Field"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Custom Field.");
        }
        await driver.findElement(By.linkText("Add Custom Field")).click();
        while ((await driver.findElements(By.id("id_field_name"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Custom Field2.");
        }
        await driver.findElement(By.id("id_field_name")).click();
        await driver.findElement(By.id("id_field_name")).sendKeys("Model");
        await driver.findElement(By.id("id_field_description")).click();
        await driver.findElement(By.id("id_field_description")).sendKeys("Required for ADCPS-J");
        await driver.findElement(By.id("id_field_type")).click();
        {
            const dropdown = await driver.findElement(By.id("id_field_type"));
            await dropdown.findElement(By.xpath("//option[. = 'Text Field']")).click();
        }

        await driver.findElement(By.id("id_field_default_value")).sendKeys("WHLS75-1500");
        await driver.findElement(By.id("id_global_for_part_types_4")).click();  //instruments
        await driver.findElement(By.css(".btn-primary")).click();

        // Add Computerized Part Type
        await driver.findElement(By.id("navbarAdmintools")).click();
        await driver.findElement(By.linkText("Edit Part Types")).click();

        await driver.findElement(By.linkText("Add Part Type")).click();
        await driver.findElement(By.id("id_name")).sendKeys("Computerized");
        await driver.findElement(By.css(".btn-primary")).click();

        // Add a Part Type with a name
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Add Part Type")).click();
        await driver.findElement(By.id("id_name")).sendKeys("Structural");
        await driver.findElement(By.css(".btn-primary")).click();

        // Add Part Type with null name
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Add Part Type")).click();
        await driver.findElement(By.css(".btn-primary")).click();
        assert(await driver.findElement(By.id("error_1_id_name")).getText() == "This field is required.");
        await driver.findElement(By.css(".btn-light")).click();

        //Add template with Part Number, Name, and Type
        await driver.findElement(By.id("navbarTemplates")).click();
        await driver.wait(until.elementLocated(By.linkText("Parts")));
        await driver.findElement(By.linkText("Parts")).click();
        //        await new Promise(r => setTimeout(r, 6000));
        while ((await driver.findElements(By.linkText("Add Part Template"))).length == 0) // 1.6
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Part Template1.");
        }

        await driver.findElement(By.linkText("Add Part Template")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_part_number")).sendKeys("123-456-789");
        await driver.findElement(By.id("id_name")).sendKeys("Coastal Mooring");
        await driver.findElement(By.id("id_friendly_name")).sendKeys("surface mooring");
        {
            dropdown = await driver.findElement(By.id("id_part_type"));
            await dropdown.findElement(By.xpath("//option[. = ' Structural']")).click();

        }
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 6000));

        var obj = await driver.findElements(By.xpath("//*[text()='Part with this Part number already exists.']"));
        if (obj.length != 0) {
            throw new Error("Please run the Delete Parts Test. Coastal Mooring already created");
        }

        await driver.findElement(By.id("navbarTemplates")).click();
        await driver.wait(until.elementLocated(By.linkText("Parts")));
        await driver.findElement(By.linkText("Parts")).click();
        while ((await driver.findElements(By.linkText("Add Part Template"))).length == 0) // 1.6
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Part Template2.");
        }
        await driver.findElement(By.linkText("Add Part Template")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_part_number")).sendKeys("555-456-789");
        await driver.findElement(By.id("id_name")).sendKeys("Surface Buoy");
        await driver.findElement(By.id("id_friendly_name")).sendKeys("buoy");
        {
            dropdown = await driver.findElement(By.id("id_part_type"));
            await dropdown.findElement(By.xpath("//option[. = ' Structural']")).click();

        }
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 6000));

        var obj = await driver.findElements(By.xpath("//*[text()='Part with this Part number already exists.']"));
        if (obj.length != 0) {
            throw new Error("Please run the Delete Parts Test. Surface Buoy already created");
        }

        await driver.findElement(By.id("navbarTemplates")).click();
        await driver.wait(until.elementLocated(By.linkText("Parts")));
        await driver.findElement(By.linkText("Parts")).click();
        while ((await driver.findElements(By.linkText("Add Part Template"))).length == 0) // 1.6
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Part Template3.");
        }

        await driver.findElement(By.linkText("Add Part Template")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_part_number")).sendKeys("666-456-789");
        await driver.findElement(By.id("id_name")).sendKeys("Wifi Template");
        await driver.findElement(By.id("id_friendly_name")).sendKeys("wifi");
        {
            dropdown = await driver.findElement(By.id("id_part_type"));
            await dropdown.findElement(By.xpath("//option[. = ' Structural']")).click();

        }
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));

        var obj = await driver.findElements(By.xpath("//*[text()='Part with this Part number already exists.']"));
        if (obj.length != 0) {
            throw new Error("Please run the Delete Parts Test. Wifi Template already created");
        }

        // Create new Template Revision with cost or refurbishment cost with greater than 2 decimal places.
        while ((await driver.findElements(By.id("action"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Part Template3.");
        }
        await driver.findElement(By.id("action")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Create New Revision")).click();
        while ((await driver.findElements(By.id("id_revision_code"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Create New Revision1.");
        }
        await new Promise(r => setTimeout(r, 2000));   //docker element not interactable
        await driver.findElement(By.id("id_revision_code")).sendKeys("B");
        await driver.findElement(By.id("id_unit_cost")).clear();
        await driver.findElement(By.id("id_unit_cost")).sendKeys("3.000");
        await driver.findElement(By.id("id_refurbishment_cost")).clear();
        await driver.findElement(By.id("id_refurbishment_cost")).sendKeys("4.000");
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));

        await driver.wait(until.elementLocated(By.css("#div_id_unit_cost .ajax-error")));
        assert(await driver.findElement(By.css("#div_id_unit_cost .ajax-error")).getText() == "Ensure that there are no more than 2 decimal places.");
        assert(await driver.findElement(By.css("#div_id_refurbishment_cost .ajax-error")).getText() == "Ensure that there are no more than 2 decimal places.");
        await driver.findElement(By.id("id_unit_cost")).clear();
        await driver.findElement(By.id("id_unit_cost")).sendKeys("9999999999.00");
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.wait(until.elementLocated(By.css("#div_id_unit_cost .ajax-error")));
        assert(await driver.findElement(By.css("#div_id_unit_cost .ajax-error")).getText() == "Ensure that there are no more than 9 digits in total.");

        // Create a new Template Revision with cost or refurbishment cost with 2 decimal places.
        await driver.findElement(By.id("id_unit_cost")).clear();
        await driver.findElement(By.id("id_unit_cost")).sendKeys("3.00");
        await driver.switchTo().frame(0);
        await driver.switchTo().defaultContent();
        await driver.findElement(By.id("id_refurbishment_cost")).clear();
        await driver.findElement(By.id("id_refurbishment_cost")).sendKeys("3.74");
        await driver.findElement(By.css(".controls > .btn")).click();
        while ((await driver.findElements(By.id("action"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Revision2.");
        }

        // Add template with null Part Number, name, type or revision code.
        await driver.findElement(By.linkText("Add Part Template")).click();
        while ((await driver.findElements(By.css(".controls > .btn"))).length == 0) // 1.6
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Null Part Number.");
        }
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));

        await driver.wait(until.elementLocated(By.css("#div_id_part_number .ajax-error")));
        await new Promise(r => setTimeout(r, 2000));
        assert(await driver.findElement(By.css("#div_id_part_number .ajax-error")).getText() == "This field is required.");
        assert(await driver.findElement(By.css("#div_id_name .ajax-error")).getText() == "This field is required.");
        assert(await driver.findElement(By.css("#div_id_part_type .ajax-error")).getText() == "This field is required.");

        // Add template with same Part Number used above.
        await driver.findElement(By.id("id_part_number")).clear();
        await driver.findElement(By.id("id_part_number")).sendKeys("123-456-789");
        await driver.wait(until.elementLocated(By.id("id_name")));
        await driver.findElement(By.id("id_name")).clear();
        await driver.findElement(By.id("id_name")).sendKeys("Coastal Mooring");
        await driver.findElement(By.id("id_friendly_name")).clear();
        await driver.findElement(By.id("id_friendly_name")).sendKeys("surface mooring");
        dropdown = await driver.findElement(By.id("id_part_type"));
        await dropdown.findElement(By.xpath("//option[. = ' Structural']")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.wait(until.elementLocated(By.css("#div_id_part_number .ajax-error")));
        assert(await driver.findElement(By.css("#div_id_part_number .ajax-error")).getText() == "Part with this Part number already exists.");

        // Create ADCPS-J Part Template
        await driver.findElement(By.id("navbarTemplates")).click();
        await driver.wait(until.elementLocated(By.linkText("Parts")));
        await driver.findElement(By.linkText("Parts")).click();
        while ((await driver.findElements(By.linkText("Add Part Template"))).length == 0) // 1.6
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add Part Template4.");
        }

        await driver.findElement(By.linkText("Add Part Template")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_part_number")).sendKeys("1336-00010-0000");
        await driver.findElement(By.id("id_name")).sendKeys("ADCPS-J");
        {
            dropdown = await driver.findElement(By.id("id_part_type"));
            await dropdown.findElement(By.xpath("//option[. = ' Instrument']")).click();

        }
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));

        var obj = await driver.findElements(By.xpath("//*[text()='Part with this Part number already exists.']"));
        if (obj.length != 0) {
            throw new Error("Please run the Delete Parts Test. ADCPS-J Template already created");
        }

        // Add & Set the Manufacturer and Model for ADCPS-J
        while ((await driver.findElements(By.linkText("Add New Field"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Add New Field.");
        }
        await driver.findElement(By.linkText("Add New Field")).click();
        await new Promise(r => setTimeout(r, 2000));
        // Find Manufacturer and Model row to select
        var i = 1;
        while (true) {
            if ((await driver.findElement(By.xpath("//div[@id='div_id_user_defined_fields']/div/div[" + i + "]/label")).getText()) == "Manufacturer") {
                break;
            }
            i++;
        }
        var j = 1;
        while (true) {
            if ((await driver.findElement(By.xpath("//div[@id='div_id_user_defined_fields']/div/div[" + j + "]/label")).getText()) == "Model") {
                break;
            }
            j++;
        }
        await driver.findElement(By.id("id_user_defined_fields_" + i)).click();
        await driver.findElement(By.id("id_user_defined_fields_" + j)).click();
        await driver.findElement(By.css(".controls > .btn-primary")).click();
        while ((await driver.findElements(By.partialLinkText("Manufacturer"))).length == 0) {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Manufacturer.");
        }
        await driver.findElement(By.partialLinkText("Manufacturer")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Set Field Value")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_field_value")).sendKeys("Teledyne RDI");
        await driver.findElement(By.css(".controls > .btn-primary")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.partialLinkText("Model")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Set Field Value")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_field_value")).sendKeys("WHLS75-1500");
        await driver.findElement(By.css(".controls > .btn-primary")).click();

        // EDIT PARTS TEST

        console.log("Edit Parts running...");
        // Change part type
        await driver.findElement(By.id("navbarAdmintools")).click();
        await driver.findElement(By.linkText("Edit Part Types")).click();
        // Get the index to the row Structural is displayed on screen
        await new Promise(r => setTimeout(r, 2000));

        if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Structural']"))).length != 0) {
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Structural") {
                    break;
                }
                i++;
            }
        }
        else
            console.log("Edit Parts failed: Structural type not found");

        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-primary")).click();

        await driver.findElement(By.id("id_name")).clear();
        await driver.findElement(By.id("id_name")).sendKeys("Structural - Updated");
        await driver.findElement(By.css(".btn-primary")).click();

        // Change part type name to null
        await new Promise(r => setTimeout(r, 2000));

        if ((await driver.findElements(By.xpath("//tr[*]/td[text()='Structural - Updated']"))).length != 0) {
            var i = 1;
            while (true) {
                if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Structural - Updated") {
                    break;
                }
                i++;
            }
        }
        else
            console.log("Edit Parts failed: Structural - Updated type not found");

        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-primary")).click();
        await driver.findElement(By.id("id_name")).clear();
        await driver.findElement(By.id("id_name")).sendKeys(" ");
        await driver.findElement(By.css(".btn-primary")).click();
        assert(await driver.findElement(By.id("error_1_id_name")).getText() == "This field is required.");

        // Change part type parent
        await driver.wait(until.elementLocated(By.id("id_name")));
        await driver.findElement(By.id("id_name")).clear();
        await driver.findElement(By.id("id_name")).sendKeys("Structural");
        await driver.findElement(By.css(".parts")).click();
        dropdown = await driver.findElement(By.id("id_parent"));
        await dropdown.findElement(By.xpath("//option[. = ' Computerized']")).click();
        await driver.findElement(By.css(".btn-primary")).click();

        {
            await new Promise(r => setTimeout(r, 2000));
            const elements = await driver.findElements(By.xpath("//td[contains(.,\'Structural\')]"));
            assert(elements.length);
        }

        // Change part type parent back to null
        // Get the index to the row Structural is displayed on screen
        await new Promise(r => setTimeout(r, 2000));  //until element located not working here
        var i = 1;
        while (true) {
            if ((await driver.findElement(By.xpath("//tr[" + i + "]/td")).getText()) == "Structural") {
                break;
            }
            i++;
        }
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.css("tr:nth-child(" + i + ") .btn-primary")).click();
        dropdown = await driver.findElement(By.id("id_parent"));
        await dropdown.findElement(By.xpath("//option[. = '---------']")).click();
        await driver.findElement(By.css(".btn-primary")).click();

        // Search for Part Templates and change Part Number
        await driver.findElement(By.id("searchbar-query")).sendKeys("Coastal Mooring");
        await driver.findElement(By.css(".btn-outline-primary:nth-child(1)")).click();        // 22 | click | linkText=123-456-789 | 
        await driver.findElement(By.linkText("123-456-789")).click();

        //        await new Promise(r => setTimeout(r, 20000)); // 1.6
        while ((await driver.findElements(By.id("action"))).length == 0) // 1.6
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Search1.");
        }

        await driver.findElement(By.id("action")).click();

        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.linkText("Edit Part Template")).click();
        while ((await driver.findElements(By.id("id_part_number"))).length == 0)
        {
            await new Promise(r => setTimeout(r, 1000));    
            console.log("Wait 2 seconds for Edit Part Template3.");
        }
        // Github Actions stale element
        var attempts = 0;
        while(attempts < 2) {
           try {
               await driver.findElement(By.id("id_part_number")).clear();   
               break;
           } catch(StaleElementException e) {}
           attempts++;
        }
        await driver.findElement(By.id("id_part_number")).sendKeys("789-456-123");
        dropdown = await driver.findElement(By.id("id_part_type"));
        await dropdown.findElement(By.xpath("//option[. = ' Computerized']")).click();
        await new Promise(r => setTimeout(r, 4000));
        await driver.findElement(By.css(".controls > .btn")).click();

        //        await new Promise(r => setTimeout(r, 20000));   
        while ((await driver.findElements(By.id("action"))).length == 0) 
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Edit Part Template4.");
        }

        // Add revision
        await driver.findElement(By.id("action")).click();
        //	await new Promise(r => setTimeout(r, 4000));
        while ((await driver.findElements(By.linkText("Create New Revision"))).length == 0) 
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Create New Revision2.");
        }
        await driver.findElement(By.linkText("Create New Revision")).click();
        await new Promise(r => setTimeout(r, 6000));
        await driver.findElement(By.id("id_revision_code")).sendKeys("B");
        await new Promise(r => setTimeout(r, 4000));
        await driver.findElement(By.css(".controls > .btn")).click();

        //	await new Promise(r => setTimeout(r, 8000)); 
        while ((await driver.findElements(By.id("action"))).length == 0) 
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for New Revision2.");
        }

        // Change template to null Part Number, name, or type
        await driver.findElement(By.id("action")).click();
        await driver.findElement(By.linkText("Edit Part Template")).click();
        //        await new Promise(r => setTimeout(r, 6000)); 
        while ((await driver.findElements(By.id("id_part_number"))).length == 0) 
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Edit Part Template5.");
        }
        await driver.findElement(By.id("id_part_number")).click();  //stale element
        await driver.findElement(By.id("id_part_number")).clear();
        await driver.findElement(By.id("id_part_number")).sendKeys("  ");
        await driver.findElement(By.id("id_name")).clear();
        await driver.findElement(By.id("id_name")).sendKeys("  ");
        dropdown = await driver.findElement(By.id("id_part_type"));
        await dropdown.findElement(By.xpath("//option[. = '---------']")).click();
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.wait(until.elementLocated(By.css("#div_id_part_number .ajax-error")));
        assert(await driver.findElement(By.css("#div_id_part_number .ajax-error")).getText() == "This field is required.");
        assert(await driver.findElement(By.css("#div_id_name .ajax-error")).getText() == "This field is required.");
        assert(await driver.findElement(By.css("#div_id_part_type .ajax-error")).getText() == "This field is required.");

        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.id("id_part_number")).clear();
        await driver.findElement(By.id("id_part_number")).sendKeys("1232");
        await driver.findElement(By.id("id_name")).sendKeys("Coastal Mooring");
        dropdown = await driver.findElement(By.id("id_part_type"));
        await dropdown.findElement(By.xpath("//option[. = ' Structural']")).click();
        await new Promise(r => setTimeout(r, 2000));
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 6000));

        var obj = await driver.findElements(By.xpath("//*[text()='Part with this Part number already exists.']"));
        if (obj.length != 0) {
            throw new Error("Please run the Delete Parts Test. Coastal Mooring already created");
        }

        // Edit revision with null code and invalid date
        await driver.findElement(By.linkText("Revision: B")).click();
        while ((await driver.findElements(By.linkText("Edit Revision"))).length == 0)
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Edit Revision3.");
        }
        await driver.findElement(By.linkText("Edit Revision")).click();
        while ((await driver.findElements(By.id("id_revision_code"))).length == 0)
        {
            await new Promise(r => setTimeout(r, 2000));
            console.log("Wait 2 seconds for Edit Revision4.");
        }
        await driver.findElement(By.id("id_revision_code")).click();  //stale element
        await driver.findElement(By.id("id_revision_code")).clear();
        await driver.findElement(By.id("id_revision_code")).sendKeys("   ");
        await driver.findElement(By.id("id_created_at")).click();
        await driver.findElement(By.id("id_created_at")).clear();
        // await driver.findElement(By.css(".glyphicon-trash")).click();  doesn't work
        // await driver.findElement(By.id("id_created_at")).sendKeys("0000"); doesn't work - gets converted to a valid date

        // Change unit cost or refurbishment cost to value with greater than 2 decimal places
        await driver.findElement(By.id("id_unit_cost")).clear();
        await driver.findElement(By.id("id_unit_cost")).sendKeys("3.000");
        await driver.findElement(By.id("id_refurbishment_cost")).clear();
        await driver.findElement(By.id("id_refurbishment_cost")).sendKeys("3.560");
        await driver.findElement(By.css(".controls > .btn")).click();
        await new Promise(r => setTimeout(r, 6000));
        assert(await driver.findElement(By.css(".ajax-error")).getText() == "This field is required.");
        assert(await driver.findElement(By.css("#div_id_unit_cost .ajax-error")).getText() == "Ensure that there are no more than 2 decimal places.");
        assert(await driver.findElement(By.css("#div_id_refurbishment_cost .ajax-error")).getText() == "Ensure that there are no more than 2 decimal places.");

        // Close browser window
        driver.quit();
    }
    catch (e) {
        console.log(e.message, e.stack);
        console.log("Add Edit Parts failed.");
        return 1;
    }

    console.log("Add Edit Parts completed.");
    return 0;


})();
