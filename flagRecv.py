import base64
import json
import time
import urllib
from http.server import BaseHTTPRequestHandler, HTTPServer

import rsa

PRIVATEKEY_PATH = "private.pem"
RECORD_PATH = "record.txt"
LPORT = 8888

priKey = rsa.PrivateKey.load_pkcs1(open(PRIVATEKEY_PATH, 'rb').read())
f = open(RECORD_PATH, 'a')


def decrypt(content):
    return rsa.decrypt(content, priKey)


class flagReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("GOTCHA!".encode())
        if self.headers['content-length']:
            data = self.rfile.read(int(self.headers['content-length']))
            value = urllib.parse.parse_qs(data)
            flag = decrypt(base64.b64decode(value[b'data'][0]))
            ip = value[b'ip'][0]
            res = json.dumps({
                "flag": flag.decode(),
                "ip": ip.decode(),
                "ts": int(time.time()),
                "time": time.asctime().split()['3']
            })
            f.write(res)
            f.write("\n")
            f.flush()


receiver = HTTPServer(("127.0.0.1", LPORT), flagReceiver)
receiver.serve_forever()
