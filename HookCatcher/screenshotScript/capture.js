var webpage = require('webpage');
var system = require('system');

var page = webpage.create();
var args = system.args;

//4 possible parameters for capture.js
var URL = 'http://google.com';//default url i sgoogle
var imgName = "screenshot.jpeg";//default image name of screenshot = screenshot.jpeg
var imgWidth = "1024";//default image size = 1024 x 768
var imgHeight = "768";


//Shell command: phantomjs capture.js <url> <imgName> <imageWidth> <imageHeight>
//!!!Need to change back to 2
if(args.length > 0) //need to provie at least screenshot URL,and  name of the screenshot to be saved as
{
	var i;
	for(i = 1; i < args.length; i++)
	{
		switch (i)
		{
			case 1:
				URL = args[1];
				break;
			case 2:
				imgName = args[2];
				break;
			case 3:
				imgWidth = args[3];
				break;
			case 4:
				imgHeight = args[4];
				break;
		}
	}

	console.log("Rendering screenshot of: " + URL + " to file: " + imgName + " with dimensions: " + imgWidth + "x" + imgHeight);


	page.onError = function(msg, trace) {

	  var msgStack = ['ERROR: ' + msg];

	  if (trace && trace.length) {
	    msgStack.push('TRACE:');
	    trace.forEach(function(t) {
	      msgStack.push(' -> ' + t.file + ': ' + t.line + (t.function ? ' (in function "' + t.function +'")' : ''));
	    });
	  }

	  console.error(msgStack.join('\n'));

	};

	page.viewportSize = { width: imgWidth, height: imgHeight };
	page.open(URL, function start(status) {

		window.setTimeout(function(){
			page.render(imgName);
			phantom.exit();
		}, 5000);

	});

}else //didn't provide required number of arguments
{
	console.log("Please provide arguments for screenshot: phantomjs capture.js <url> <imgName> <imageWidth> <imageHeight>.");
}
