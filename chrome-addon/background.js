var webappUrl = "https://flasktest-uaxpuwzs5q-uw.a.run.app";
//var webappUrl = "http://dockerbuntu:8080";
var uid = undefined;
var isAuthenticated = false;

// On load, get/generate UID, then see if we have authentication
getUid();

function getUid()
{
    chrome.storage.sync.get('uid', function(items)
    {
        uid = items.uid;
        if (!uid)
        {
            var randomPool = new Uint8Array(32);
            crypto.getRandomValues(randomPool);
            var hex = '';
            for (var i = 0; i < randomPool.length; i++)
            {
                hex += randomPool[i].toString(16);
            }
            uid = hex;
            chrome.storage.sync.set({"uid" : uid}, function() { console.log("Saved new uid " + uid); })
        }
        getAuthentication(uid);
    });
}

enableTabListener = function()
{
    chrome.tabs.onUpdated.addListener(isAuthenticationTabDetected);
}

disableTabListener = function()
{
    chrome.tabs.onUpdated.removeListener(isAuthenticationTabDetected);
}

isAuthenticationTabDetected = function(tabId, changeInfo, tab)
{
    var pattern = new RegExp("https:\\/\\/flasktest-uaxpuwzs5q-uw\\.a\\.run\\.app\\/discord\\?code=\\w+&state=\\w+$");
    if (pattern.test(changeInfo.url))
    {
        // TODO: Validate here!!
        console.log("Detected auth tab!!");
        console.log("Detected successful authentication message");
        isAuthenticated = true;
        disableTabListener();
    }
}

function getAuthentication(uid)
{
    if (!isAuthenticated)
    {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function()
        {
            if (xhr.readyState == 4 && xhr.status == 200)
            {
                json = xhr.response;
                if (json.auth == "success")
                {
                    console.log("UID " + uid + " is authenticated!");
                    isAuthenticated = true;
                }
                else
                {
                    console.log("UID " + uid + " is not yet authenticated. Will attempt authentication now");
                    isAuthenticated = false;
                    authenticate();
                }
            }
        }
        xhr.responseType = 'json';
        xhr.open("GET", webappUrl + "/check_auth?uid=" + uid);
        xhr.send();
    }
}

getStateKey = function(uid, callback)
{
    // TODO: Save state key
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function()
    {
        if (xhr.readyState == 4 && xhr.status == 200)
        {
            console.log("Got state key from server: " + xhr.responseText)
            chrome.storage.sync.set({"state": xhr.responseText})
            callback(uid, xhr.responseText);
        }
    }
    xhr.open("GET", webappUrl + "/genstate?uid=" + uid);
    xhr.send();
}

discordAuthRedirect = function(uid, stateKey)
{
    console.log("Sending discord auth request with uid " + uid + " and statekey " + stateKey);
    var discordAuthUrl = "https://discordapp.com/api/oauth2/authorize?client_id=701591092730134528&redirect_uri=https%3A%2F%2Fflasktest-uaxpuwzs5q-uw.a.run.app%2Fdiscord&response_type=code&scope=identify&state=" + stateKey;
    chrome.tabs.create({ url: discordAuthUrl});
}

authenticate = function()
{
    console.log("UID:" + uid);
    enableTabListener();
    getStateKey(uid, discordAuthRedirect);
}

sendToDiscord = function(url)
{
    if (isAuthenticated)
    {
        var linkUrl = url.linkUrl;
        var endIdx = linkUrl.indexOf('&');
        if (endIdx > 0)
        {
            linkUrl = linkUrl.slice(0,endIdx);
        }
        linkUrl = encodeURI(linkUrl);
        var jsonObject = '{ "uid": "' + uid + '", "songurl": "' + linkUrl + '"}';
        var xhr = new XMLHttpRequest();
        xhr.open("POST", webappUrl + "/play",  true);
        xhr.setRequestHeader("Content-Type", "application/json");
        console.log("sending " + linkUrl + " with content " + jsonObject);
        xhr.send(jsonObject);
	}
}

chrome.contextMenus.create(
{
	"title": "Send to discord",
	"contexts": ["link"],
	"onclick" : sendToDiscord,
	"documentUrlPatterns":["http://*.youtube.com/*", "https://*.youtube.com/*", "http://youtube.com/*", "https://youtube.com/*"]
});
