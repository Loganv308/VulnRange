# Internal-only mock "cloud metadata" service. Not published to the host -- reach it via SSRF.
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

ROUTES = {
    "/": "latest/\n",
    "/latest/": "meta-data/\n",
    "/latest/meta-data/": "hostname\niam/\n",
    "/latest/meta-data/hostname": "devportal-prod-01\n",
    "/latest/meta-data/iam/": "security-credentials/\n",
    "/latest/meta-data/iam/security-credentials/": "devportal-role\n",
    "/latest/meta-data/iam/security-credentials/devportal-role":
        '{"AccessKeyId":"AKIALABFAKE0000","SecretAccessKey":"' + os.environ.get("FLAG_SSRF", "") + '"}\n',
}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = ROUTES.get(self.path)
        self.send_response(200 if body else 404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write((body or "not found\n").encode())


HTTPServer(("0.0.0.0", 8080), H).serve_forever()
