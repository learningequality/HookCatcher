var webpage = require('webpage');
var page = webpage.create();
var URL = 'http://localhost:8000/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5';

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

//page.viewportSize = { width: 1024, height: 768 };
page.open(URL, function start(status) {

	window.setTimeout(function(){
		page.render('exlore.jpeg');
		phantom.exit();
	}, 5000);

});
