import http.client, struct, os
import base64, subprocess
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import json, tempfile
from time import sleep
from random import randint

class RemoteChromium:
    def __init__(self) -> None:
        self.running = False
        self.debugPort = randint(2000, 6500)
        self.baseURL = "http://localhost:{}".format(self.debugPort)
        self.isWindows = os.name == "nt"

    def sendWSMessage(self, url, message):
        URL = urlparse(url)
        port = URL.port if URL.port is not None else (443 if URL.scheme == 'wss' else 80)
        hostname = URL.netloc.split(':')[0] if URL.hostname is None else URL.hostname
        if URL.scheme == 'wss':
            conn = http.client.HTTPSConnection(hostname, port)
        else:
            conn = http.client.HTTPConnection(hostname, port)

        key = base64.b64encode(b'random_key').decode()

        request_headers = {
            'Accept': '*/*',
            'Sec-Fetch-Dest': 'websocket',
            'Sec-Fetch-Mode': 'websocket',
            'Host': URL.netloc,
            'Upgrade': 'websocket',
            'Connection': 'keep-alive, Upgrade',
            'Sec-WebSocket-Key': key,
            'Sec-WebSocket-Version': '13',
            'Sec-WebSocket-Extensions': 'permessage-deflate'
        }
        
        conn.request('GET', URL.path, headers=request_headers)

        response = conn.getresponse()

        if response.status != 101:
            raise Exception('WebSocket handshake failed')

        sock = conn.sock

        encoded_message = message.encode()

        masked_payload = bytearray()
        
        masking_key = b"\x12\x34\x56\x78"

        for i in range(len(encoded_message)):

            masking_key_byte = masking_key[i % 4]
            
            masked_byte = encoded_message[i] ^ masking_key_byte
            
            masked_payload.append(masked_byte)

        pLen = len(encoded_message)

        if pLen <= 125:
            payload = bytearray([0x81, int("1" + bin(pLen)[2:], 2)]) + masking_key + masked_payload
        elif pLen <= 64000:
            payload = bytearray([0x81, int("1" + bin(126)[2:], 2)]) + struct.pack('>H', pLen) + masking_key + masked_payload
        else:
            lenBin = pLen.to_bytes(8, byteorder='big')

            payload = bytearray([0x81, int("1" + bin(127)[2:], 2)]) + lenBin + masking_key + masked_payload

        sock.sendall(payload)

        sock.close()

    def getTabs(self):
        if self.running:
            resp = urlopen("{}/json/list".format(self.baseURL))
            allTabs =  json.loads(resp.read())
            tabs = []
            for t in allTabs:
                if t['type'].lower() == 'page':
                    tabs.append(t)
            return tabs
        else:
            raise Exception('Chromium is not running')
    
    def openTab(self, url):
        if self.running:
            req = Request("{}/json/new?{}".format(self.baseURL, url), method="PUT")
            resp = urlopen(req)
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
            else:
                return None
        else:
            raise Exception('Chromium is not running')
    
    def executeJS(self, tab, statement):
        self.sendWSMessage(tab["webSocketDebuggerUrl"], json.dumps({
              'id': 1,
              'method': 'Runtime.evaluate',
              'params': {
                  'expression': statement
              }
            })
        )
    
    def setJSONCookie(self, tab, cookie):
        self.sendWSMessage(tab["webSocketDebuggerUrl"], json.dumps({
              'id': 1,
              'method': 'Network.setCookie',
              'params': cookie
            })
        )

    def getInstalledBrowser(self):
        if self.isWindows:
            return "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        else:
            try:
                subprocess.Popen(["chromium", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "chromium"
            except:
                try:
                    subprocess.Popen(["chrome", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return "chrome"
                except:
                    raise Exception("No browser found (chrome or chromium must be installed)")
 
    def start(self):
        subprocess.Popen([self.getInstalledBrowser(), "--remote-debugging-port={}".format(self.debugPort), "--remote-allow-origins=*", "--user-data-dir={}".format(tempfile.mkdtemp())],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL
        )
        while True:
            try:
                urlopen("{}/json/list".format(self.baseURL))
                self.running = True
                break
            except:
                pass
            sleep(1)
