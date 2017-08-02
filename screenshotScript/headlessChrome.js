const chromeLauncher = require('chrome-launcher');
const CDP = require('chrome-remote-interface');
const argv = require('minimist')(process.argv.slice(2));
const file = require('fs');

// Args
const url = argv.url || 'https://www.google.com';
const format = argv.format === 'jpeg' ? 'jpeg' : 'png';
const viewportWidth = parseInt(argv.viewportWidth) || 1366;
const viewportHeight = parseInt(argv.viewportHeight) || 768;
const delay = argv.delay || 5000;
const imgName = argv.imgName || url;


/**
 * Launches a debugging instance of Chrome.
 * @param {boolean=} headless True (default) launches Chrome in headless mode.
 *     False launches a full version of Chrome.
 * @return {Promise<ChromeLauncher>}
 */
function launchChrome(headless=true) {
  return chromeLauncher.launch({
    // port: 9222, // Uncomment to force a specific port of your choice.
    chromeFlags: [
      '--windows-size=1024,2000',
      '--hide-scrollbars',
      '--disable-gpu',
      headless ? '--headless' : ''
    ]
  });
}



(async function() {

const chrome = await launchChrome();
const protocol = await CDP({port: chrome.port});

  const {DOM, Emulation, Network, Page, Runtime} = protocol;

  // Enable events on domains we are interested in.
  await Page.enable();
  await DOM.enable();
  await Network.enable();
  
  // Navigate to target page
  frameID = await Page.navigate({url});

  //create device to get full content height
  const deviceMetrics = {
    width: viewportWidth,
    height: viewportHeight,
    deviceScaleFactor: 0,
    mobile: false,
    fitWindow: false,
  };


  // Wait for page load event to take screenshot
  Page.loadEventFired(async () => {

    // If the `full` CLI option was passed, we need to measure the height of all content
    const pageMetric = await Page.getLayoutMetrics();
    height = pageMetric.contentSize.height;

   /* Another way of calculating content height returns same value as contentSize
    const result = await Runtime.evaluate({ expression: `Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight)` });
    console.log(result.result.value);*/

    // new device metrics for emulation
    const newMetrics = {
      width: viewportWidth,
      height: height,
      deviceScaleFactor: 0,
      mobile: false,
      fitWindow: false,
    };
    await Emulation.setDeviceMetricsOverride(newMetrics);
    await Emulation.setVisibleSize({width: viewportWidth, height: height});

    setTimeout(async function() {
      const base64img = await Page.captureScreenshot({format:format, fromSurface: true});
      file.writeFile(imgName, base64img.data, 'base64', function(err) {
        if (err) {
          console.error(err);
        } else {
          console.log('Screenshot saved: ' + imgName);
        }
        protocol.close();
        chrome.kill();
      });
    }, delay);
  });

})();