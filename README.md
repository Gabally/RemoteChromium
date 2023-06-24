# RemoteChromium
Simple python class to control a chromium browser with no external dependencies (only chromium must be installed)

### Example Usage
``` py
from RemoteChromium import RemoteChromium

chr = RemoteChromium()

chr.start()

tab = chr.openTab("https://example.com")

chr.executeJS(tab, 'alert(1)')

chr.setJSONCookie(tab, {
    "name": "test",
    "value": "lol" * 200,
    "url": "https://example.com/",
    "domain": "example.com",
    "path": "/",
    "secure": True,
    "httpOnly": True, 
    "priority": "Medium"
})
``` 