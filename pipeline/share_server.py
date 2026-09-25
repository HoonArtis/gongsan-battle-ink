# 공유 폴더 하나만 서비스하는 작은 HTTP 서버(영상 탐색용 Range 요청 지원). 127.0.0.1 전용 — 외부 공개는 cloudflared가 맡는다.
# 실행: python share_server.py <폴더> <포트>
import sys, os, re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        size = os.path.getsize(path)
        start = int(m.group(1)) if m and m.group(1) else 0
        end = int(m.group(2)) if m and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416); return None
        f = open(path, 'rb'); f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        self._remaining = end - start + 1
        return f
    def copyfile(self, src, dst):
        n = getattr(self, '_remaining', None)
        if n is None: return super().copyfile(src, dst)
        while n > 0:
            b = src.read(min(1 << 16, n))
            if not b: break
            try: dst.write(b)
            except (ConnectionResetError, BrokenPipeError): break
            n -= len(b)
    def list_directory(self, path):
        self.send_error(404); return None
    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes'); super().end_headers()

folder, port = sys.argv[1], int(sys.argv[2])
ThreadingHTTPServer(('127.0.0.1', port), partial(RangeHandler, directory=folder)).serve_forever()
