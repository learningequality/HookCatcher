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
const urlParts = url.split('#');
const targetURL = urlParts[0];

const host = targetURL.substring(0, (targetURL.indexOf('.org/') + 5)); // just the host name
const signinPath = 'user';
const signinURL = host + signinPath;

function validURL(value) {
  return /^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:[/?#]\S*)?$/i.test(value);
}

if (! (validURL(url) && validURL(targetURL)) ){
  console.log(argv.url)
  console.log("Puppeteer: URL '" + url + "'is not a valid URL for screenshotting");
  process.exit(1);
}

(async () => {
    const browser = await puppeteer.launch({headless: true});
    const page = await browser.newPage();
    await page.setViewport({width: imgWidth, height: imgHeight});

    if (validURL(signinURL)){
      console.log('configuring UI for ' + signinURL);
      // First, go directly to the sign in page to login then the target pages
      // In the case that going to the singinURL takes you to an incorrect page, try going directly
      try{
        await page.goto(signinURL, {waitUntil: 'networkidle2'});
        // interact with UI
        await page.type('input[type=text]', 'devowner');
        await page.type('input[type=password]', 'admin123');

        await page.click('button[type=submit]', {waitUntil: 'networkidle2'});
        await page.waitForNavigation({waitUntil: 'networkidle2'});  // button redirects
      }catch (e){}
    }

    try{
      // ERROR: returns Timeout error when attempting to GOTO url with '#' within the url
      // the page actually loads but just never finishes the idle
      // Just ignore this error because it's expected
      console.log('actual page ' + url);
      await page.goto(url, {timeout: 3000});
      //wait 2 second if still same url wait till navigation over
      console.log(page.url())
      if (page.url() == url){
        await page.waitForNavigation({timeout: 3000, waitUntil: 'networkidle2'});
      }else{
        await page.waitForNavigation({timeout: 3000, waitUntil: 'networkidle2'});
        const calc_height = await page.evaluate(() => {
          return Math.max(document.body.scrollHeight,
                          document.body.offsetHeight,
                          document.documentElement.clientHeight,
                          document.documentElement.scrollHeight,
                          document.documentElement.offsetHeight);
          });

        //await page.setViewport({width: 600, height: calc_height});  Another way of calc height

        console.log('Early exit: saving screenshot to: ' + imgName);
        await page.screenshot({path: imgName, type: 'png', fullPage: true});
        await page.close();
        await browser.close();
        process.exit(1);

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
