var webpage = require('webpage');
var system = require('system');

var page = webpage.create();
var args = system.args;
var URL = 'http://localhost:8000/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5';
var imgName = "screenshot.jpeg";//default image name of screenshot = screenshot.jpeg
var imgWidth = "1024";//default image size = 1024 x 768
var imgHeight = "768";

if(args.length > 1)
{
	imgName = args[1];
	if(args.length >= 4)
	{
		imgWidth = args[2];
		imgHeight = args[3];
	}

	console.log("Rendering screenshot of " + imgName + " with dimensions " + imgWidth + "x" + imgHeight);
}else
{
	console.log("Please provide arguments for screenshot: phantom.js capture.js <fileName> <imageWidth> <imageHeight>.");
}

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

page.viewportSize = { width: 1024, height: 768 };
page.open(URL, function start(status) {

	window.setTimeout(function(){
		page.render(imgName);
		phantom.exit();
	}, 5000);

});
