#!/usr/bin/env python3
"""LUNE Apps — Servidor dos apps Look Gen + Copy Gen
   Proxy da API Anthropic com key embutida
"""

import http.server
import json
import urllib.request
import ssl
import os

PORT = int(os.environ.get('PORT', 9000))
ANTHROPIC_KEY = open(os.path.expanduser('~/.anthropic_key')).read().strip() if os.path.exists(os.path.expanduser('~/.anthropic_key')) else os.environ.get('ANTHROPIC_KEY', '')

SSL_CTX = ssl.create_default_context()

# Carregar HTMLs em memória
APP_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(APP_DIR, 'look-gen.html'), 'r') as f:
    LOOK_HTML = f.read()

with open(os.path.join(APP_DIR, 'copy-gen.html'), 'r') as f:
    COPY_HTML = f.read()

INDEX_HTML = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LUNE Apps</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', sans-serif; background: #F5F0E8; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
  .container { text-align: center; padding: 2rem; }
  h1 { font-family: 'Cormorant Garamond', serif; font-size: 3rem; color: #1B4D3E; margin-bottom: 0.5rem; }
  p { color: #888; margin-bottom: 2rem; font-size: 0.9rem; }
  .apps { display: flex; gap: 1.5rem; flex-wrap: wrap; justify-content: center; }
  a.card { display: block; background: white; border-radius: 12px; padding: 2rem 2.5rem; text-decoration: none; color: #2A2A2A; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: all 0.2s; min-width: 220px; }
  a.card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(27,77,62,0.15); }
  .card .icon { font-size: 2rem; margin-bottom: 0.8rem; }
  .card h2 { font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; color: #1B4D3E; margin-bottom: 0.3rem; }
  .card .desc { font-size: 0.8rem; color: #888; }
</style>
</head>
<body>
<div class="container">
  <h1>LUNE</h1>
  <p>Apps de criação</p>
  <div class="apps">
    <a class="card" href="/look">
      <div class="icon">👗</div>
      <h2>Look Generator</h2>
      <div class="desc">3 looks LUNE a partir de referência</div>
    </a>
    <a class="card" href="/copy">
      <div class="icon">✍️</div>
      <h2>Copy Gen</h2>
      <div class="desc">Ads com framework Khayat</div>
    </a>
  </div>
</div>
</body>
</html>'''


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index':
            self._serve_html(INDEX_HTML)
        elif self.path == '/look':
            self._serve_html(LOOK_HTML)
        elif self.path == '/copy':
            self._serve_html(COPY_HTML)
        elif self.path == '/health':
            self._serve_json({'status': 'ok', 'apps': ['look-gen', 'copy-gen']})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/messages':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)

            try:
                req = urllib.request.Request(
                    'https://api.anthropic.com/v1/messages',
                    data=body,
                    headers={
                        'Content-Type': 'application/json',
                        'x-api-key': ANTHROPIC_KEY,
                        'anthropic-version': '2023-06-01'
                    }
                )
                resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=60)
                result = resp.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(result)
            except Exception as e:
                error = json.dumps({'error': {'message': str(e)}})
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(error.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key, anthropic-version')
        self.end_headers()

    def _serve_html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode())

    def _serve_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        print(f"[LUNE Apps] {args[0]}")


if __name__ == '__main__':
    if not ANTHROPIC_KEY:
        print('ERRO: Faltando ANTHROPIC_KEY (~/.anthropic_key ou env)')
        exit(1)

    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'\n🎨 LUNE Apps — http://localhost:{PORT}')
    print(f'   /look  — Look Generator')
    print(f'   /copy  — Copy Gen (Khayat)')
    print(f'   Key: ...{ANTHROPIC_KEY[-8:]}')
    print(f'   Ctrl+C pra parar\n')
    server.serve_forever()
