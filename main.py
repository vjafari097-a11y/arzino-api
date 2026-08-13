import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# آدرس‌های دریافت قیمت
URLS = [
    "https://call1.tgju.org/ajax.json",
    "https://call2.tgju.org/ajax.json"
]

def get_prices():
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                current = data.get("current", {})
                
                # استخراج قیمت دلار
                dollar_raw = current.get("price_dollar_rl", {}).get("p")
                dollar = int(float(str(dollar_raw).replace(",", ""))) if dollar_raw else None
                
                # استخراج قیمت طلای ۱۸ عیار
                gold_raw = current.get("geram18", {}).get("p")
                gold = int(float(str(gold_raw).replace(",", ""))) if gold_raw else None
                
                return {
                    "dollar": dollar,
                    "dollar_toman": dollar // 10 if dollar else None,
                    "gold18": gold,
                    "gold18_toman": gold // 10 if gold else None,
                    "status": "ok"
                }
        except Exception:
            continue
    return {"status": "error", "message": "Could not fetch prices"}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # جلوگیری از خطای CORS
        self.end_headers()
        
        if self.path == '/prices':
            result = get_prices()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.wfile.write(json.dumps({"status": "ok", "message": "Arzino API is running"}).encode())

if name == "__main__":
    # رندر پورت رو از طریق متغیر محیطی PORT به ما میده
    port = int(os.environ.get("PORT", 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()
