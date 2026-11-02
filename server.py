# -*- coding: utf-8 -*-
"""
中文输入法 Web 服务端（纯标准库）。

启动：  python server.py
访问：  http://localhost:8081
首次启动会构建拼音索引（约几秒~几十秒，取决于是否安装 pypinyin），之后读缓存秒开。
"""
import os
import json
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import config
import engine
import llm_hook

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
HOST = "0.0.0.0"
PORT = int(os.environ.get("IME_PORT", "8081"))


def ensure_engine():
    try:
        return engine.build()
    except Exception as e:
        return {"error": str(e)}


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        if route in ("/", "/index.html"):
            self._send_file(os.path.join(WEB_DIR, "index.html"), "text/html; charset=utf-8")
        elif route == "/static/app.js":
            self._send_file(os.path.join(WEB_DIR, "app.js"), "application/javascript; charset=utf-8")
        elif route == "/static/style.css":
            self._send_file(os.path.join(WEB_DIR, "style.css"), "text/css; charset=utf-8")
        elif route == "/api/info":
            self._send_json(engine.info())
        elif route == "/api/llm_status":
            self._send_json({"available": llm_hook.is_available(force=True)})
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            body = {}

        if parsed.path == "/api/query":
            pinyin = body.get("pinyin", "")
            context = body.get("context", "")
            cands = engine.decode(pinyin, config.TOP_K)
            assoc = engine.associate(context, config.TOP_K)
            llm_on = llm_hook.is_available()
            # 仅在“拼音清空、看续写”的场景调用 AI，打字过程中不过度请求
            llm = llm_hook.suggest(context, 5) if (llm_on and not pinyin and context) else []
            self._send_json({
                "candidates": cands,
                "associate": assoc,
                "llm_available": llm_on,
                "llm": llm,
            })
        elif parsed.path == "/api/associate":
            context = body.get("context", "")
            self._send_json({"associate": engine.associate(context, config.TOP_K)})
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


def main():
    stats = ensure_engine()
    if "error" in stats:
        print("[输入法] 构建词库失败：", stats["error"])
        print("请确认 THUOCL 词库路径正确（config.THUOCL_DATA_DIR 或环境变量 THUOCL_DATA）。")
    else:
        print("[输入法] 词库加载完成：", stats)
    print("[输入法] 正在启动服务 http://localhost:%d ..." % PORT)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[输入法] 已停止。")


if __name__ == "__main__":
    main()
