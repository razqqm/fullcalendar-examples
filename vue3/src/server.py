from http.server import SimpleHTTPRequestHandler, HTTPServer
import json

FILENAME = 'events.json'

class CustomHandler(SimpleHTTPRequestHandler):

    def _send_cors_headers(self):
        """ Sends CORS headers for preflight requests """
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/events':
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with open(FILENAME, 'r') as file:
                events = [json.loads(line) for line in file]
                self.wfile.write(json.dumps(events).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/events':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            events = json.loads(post_data.decode())
            with open(FILENAME, 'w') as file:
                for event in events:
                    file.write(json.dumps(event) + '\n')
            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 3000), CustomHandler)
    print('Starting server on port 3000...')
    server.serve_forever()
