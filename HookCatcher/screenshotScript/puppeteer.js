/*
Things to note.

Kolibri max html/body height is < a middle overflow div so the full page screenshot
will not work if just max-ing document, body

For some reason GOTO doesn't like how the url has a hash excpet for 'classes'
http://grammar-demo.learningequality.org/management/#/classes
*/

const puppeteer = require('puppeteer');
const argv = require('minimist')(process.argv.slice(2));

// Args
// const host = 'http://mitblossoms-demo.learningequality.org/management/facility#/data';
const url = argv.url;
const imgName = argv.imgName || url;
const imgWidth  = argv.imgWidth || 800;
const imgHeight = argv.imgHeight || 600;

//extract host for Sign In URL
const host = getHostName(url); // just the host name
const signinPath = '/user/#/signin';
const signinURL = host + signinPath;

function getHostName(url) {
    var match = url.match(/(ftp|http|https):\/\/(www[0-9]?\.)?(.[^/:]+)/i);
    if (match != null && match.length > 3 && typeof match[3] === 'string' && match[3].length > 0) {
      return match[1] + '://' + match[3];
    }
    else {
        return null;
    }
}

function validURL(s) {
    var regexp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
    return regexp.test(s);
}

if (! (validURL(url) && validURL(signinURL)) ){
  console.log("Puppeteer: URL '" + url + "'is not a valid URL for screenshotting");
  process.exit(1);
}

(async () => {
    const browser = await puppeteer.launch({headless: false});
    const page = await browser.newPage();
    await page.setViewport({width: imgWidth, height: imgHeight});

    if (validURL(signinURL) && signinURL != url){
      console.log('configuring UI for ' + signinURL);
      // First, go directly to the sign in page to login then the target pages
      // In the case that going to the singinURL takes you to an incorrect page, try going directly
      try{
        await page.goto(signinURL, {timeout: 10000, waitUntil: 'networkidle2'});
        // interact with UI
        await page.type('input[type=text]', 'devowner');
        await page.type('input[type=password]', 'admin123');

        await page.click('button[type=submit]');
        await page.waitForNavigation({timeout: 10000, waitUntil: 'domcontentloaded'});  // button redirects
      }catch (e){
      }
    }

    try{
      // ERROR: returns Timeout error when attempting to GOTO url with '#' within the url
      // the page actually loads but just never finishes the idle
      // Just ignore this error because it's expected
      console.log('actual page: ' + url);
      // BOTTTLE NECK IS IN THIS LINE BELOW TO WAIT UNTIL PAGE HAS FULLLY LOADED
      await page.goto(url, {timeout: 10000, waitUntil: 'networkidle0'}).catch((error) => {console.log(error)});

      if (page.url() != url){
        console.log('The url provided was not valid and the page redirected to: ' + page.url());
      }
    }catch (e){}

  // Attempting to calculate the full height of the page
  const calc_height = await page.evaluate(() => {
    return Math.max(document.body.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.clientHeight,
                    document.documentElement.scrollHeight,
                    document.documentElement.offsetHeight);
  });

  //await page.setViewport({width: 600, height: calc_height});  Another way of calc height

  console.log('Saving screenshot to: ' + imgName);
  await page.screenshot({path: imgName, type: 'png', fullPage: true});
  await page.close();
  await browser.close();
})();
