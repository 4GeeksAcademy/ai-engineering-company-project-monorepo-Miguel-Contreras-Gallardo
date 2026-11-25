#!/usr/bin/env python3
"""Servidor HTTP simple con soporte SPA, redirección y proxy de API."""
import argparse
import http.client
import http.server
import os
import urllib.parse

API_PROXY_PREFIX = "/api"
# Upstream de la API: mismo host/puerto del backend dentro del contenedor/Codespace.
# Se puede sobreescribir con variables de entorno.
API_UPSTREAM_HOST = os.getenv("TRACKFLOW_API_HOST", "localhost")
API_UPSTREAM_PORT = int(os.getenv("TRACKFLOW_API_PORT", "8000"))

# Cabeceras hop-by-hop que no deben reenviarse aguas arriba ni abajo.
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade",
}


class TrackFlowHandler(http.server.SimpleHTTPRequestHandler):
    subdir = ""  # Se setea desde --dir

    def translate_path(self, path):
        path = super().translate_path(path)
        # Si la ruta es la raíz, servimos el subdirectorio
        if path == self.directory:
            return os.path.join(path, self.subdir.lstrip("/"), "index.html")
        return path

    # ── Proxy de API: /api/* → upstream (localhost:8000) quitando el prefijo ──
    def _is_api_request(self, path):
        return path == API_PROXY_PREFIX or path.startswith(API_PROXY_PREFIX + "/")

    def _proxy_api(self, method):
        parsed = urllib.parse.urlparse(self.path)
        upstream_path = parsed.path[len(API_PROXY_PREFIX):] or "/"
        if parsed.query:
            upstream_path = f"{upstream_path}?{parsed.query}"

        # Leer cuerpo (POST/PUT/PATCH reenvían el body del navegador).
        body = None
        content_length = self.headers.get("Content-Length")
        if content_length:
            try:
                body = self.rfile.read(int(content_length))
            except (ValueError, OSError):
                body = None

        conn = http.client.HTTPConnection(API_UPSTREAM_HOST, API_UPSTREAM_PORT, timeout=60)
        try:
            # Reenviar cabeceras útiles (sin hop-by-hop ni Host: lo fija http.client).
            headers = {}
            for key, value in self.headers.items():
                if key.lower() in HOP_BY_HOP_HEADERS or key.lower() == "host":
                    continue
                headers[key] = value

            conn.request(method, upstream_path, body=body, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read()

            # Reenviar status y cabeceras de respuesta (preserva las CORS del backend).
            self.send_response(resp.status, resp.reason)
            for key, value in resp.getheaders():
                if key.lower() in HOP_BY_HOP_HEADERS or key.lower() == "content-length":
                    continue  # Content-Length se recalcula
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            if resp_body:
                self.wfile.write(resp_body)
        except (http.client.HTTPException, OSError) as exc:
            self.send_error(502, f"API no disponible: {exc}")
        finally:
            conn.close()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # Proxy de API
        if self._is_api_request(parsed.path):
            self._proxy_api("GET")
            return

        # Redirigir / → /subdir/
        if parsed.path == "/" or parsed.path == "":
            self.send_response(302)
            self.send_header("Location", f"/{self.subdir}/")
            self.end_headers()
            return

        # Para SPA: si la ruta no tiene extensión y no es /subdir/, servir index.html
        if not os.path.splitext(parsed.path)[1] and not parsed.path.startswith(f"/{self.subdir}/"):
            # Es una ruta SPA (como /inventory, /dashboard, etc.)
            index_path = os.path.join(self.directory, self.subdir.lstrip("/"), "index.html")
            if os.path.exists(index_path):
                self.send_response(200)
                # Detectar tipo MIME
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if self._is_api_request(parsed.path):
            self._proxy_api("POST")
            return
        return super().do_POST()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        if self._is_api_request(parsed.path):
            self._proxy_api("PUT")
            return
        return super().do_PUT()

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        if self._is_api_request(parsed.path):
            self._proxy_api("PATCH")
            return
        return super().do_PATCH()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if self._is_api_request(parsed.path):
            self._proxy_api("DELETE")
            return
        return super().do_DELETE()

    def do_OPTIONS(self):
        # Pasar el preflight al backend para que emita las cabeceras CORS correctas.
        parsed = urllib.parse.urlparse(self.path)
        if self._is_api_request(parsed.path):
            self._proxy_api("OPTIONS")
            return
        return super().do_OPTIONS()


def main():
    parser = argparse.ArgumentParser(description="TrackFlow HTTP Server")
    parser.add_argument("--port", type=int, required=True, help="Puerto")
    parser.add_argument("--dir", type=str, required=True, help="Subdirectorio a servir (backoffice o website)")
    args = parser.parse_args()

    # Directorio base: uis/
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    TrackFlowHandler.subdir = args.dir
    TrackFlowHandler.directory = base_dir

    os.chdir(base_dir)

    server = http.server.HTTPServer(("0.0.0.0", args.port), TrackFlowHandler)
    print(f"Sirviendo {args.dir} en http://0.0.0.0:{args.port}/")
    print(f"Proxy API: {API_PROXY_PREFIX}/* → http://{API_UPSTREAM_HOST}:{API_UPSTREAM_PORT}/*")
    server.serve_forever()


if __name__ == "__main__":
    main()