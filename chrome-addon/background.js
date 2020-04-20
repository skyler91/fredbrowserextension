function sendToDiscord(url) {
	var linkUrl = url.linkUrl;
	var endIdx = linkUrl.indexOf('&');
	if (endIdx > 0)
	{
		linkUrl = slice(0,endIdx);
	}
	linkUrl = encodeURI(url.linkUrl);
	var discordUrl = "https://discordapp.com/api/webhooks/701595157849440256/Q1pbHHU65y9aY0wafWxXzYFTV_c30Q_VwJbUKn3A5rYLAKCH8qS9jI08CH8WkAiJ25No";
	var xhr = new XMLHttpRequest();
	xhr.open("POST", discordUrl,  true);
	xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
	console.log("sending " + linkUrl);
	xhr.send("content=!play " + linkUrl);
}

chrome.contextMenus.create({
	"title": "Send to discord",
	"contexts": ["link"],
	"onclick" : sendToDiscord,
	"documentUrlPatterns":["http://*.youtube.com/", "https://*.youtube.com/", "http://youtube.com/", "https://youtube.com/"]
});


function test() {
	console.log("test2");
}
