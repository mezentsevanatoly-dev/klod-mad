# -*- coding: utf-8 -*-
"""Вывод жабы в браузере: http://127.0.0.1:8766/  (вкладки: Айлина, Кимпи). Читает claude_game.log каждой жабы, сервер только читает.
Запуск: python -X utf8 tools/jmc_web.py   (порт 8766, --port N). Ничего не отправляет в игру."""
import os, sys, json, http.server, socketserver, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
CHARS = {"ailina": ("Айлина", os.path.join(BASE, "JMC БОТ АЙЛИНА", "claude_game.log")),
         "kimpi": ("Кимпи", os.path.join(BASE, "JMC БОТ ИНКА", "claude_game.log"))}
PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8766

PAGE = r"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Жаба: вывод</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0e1116;--fg:#d6dde6;--mut:#7d8896;--acc:#5ab0ff;--card:#161b22;--bad:#ff6b6b;--ok:#6bd68a;--warn:#e7c35a}
@media (prefers-color-scheme: light){:root{--bg:#f5f6f8;--fg:#1d2430;--mut:#667085;--acc:#1760c9;--card:#fff;--bad:#c0392b;--ok:#1c8a4a;--warn:#9a6b00}}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:13px/1.35 Consolas,Menlo,monospace}
header{display:flex;gap:8px;align-items:center;padding:8px 12px;background:var(--card);position:sticky;top:0;flex-wrap:wrap}
button,label{font:inherit;color:var(--fg)} button{background:transparent;border:1px solid var(--mut);border-radius:6px;padding:3px 10px;cursor:pointer}
button.on{border-color:var(--acc);color:var(--acc)}
#log{padding:8px 12px 40px;white-space:pre-wrap;word-break:break-word}
.l{display:block}.step{color:var(--acc)}.bad{color:var(--bad)}.ok{color:var(--ok)}.warn{color:var(--warn)}.cmd{color:var(--warn)}.prompt{color:var(--mut)}
#st{margin-left:auto;color:var(--mut)}
</style></head><body>
<header>
 <span id="tabs"></span>
 <label><input type="checkbox" id="pr"> показывать строки-приглашения (HP/MP)</label>
 <label><input type="checkbox" id="fl" checked> следить за низом</label>
 <button id="clr">очистить экран</button><span id="st"></span>
</header><div id="log"></div>
<script>
const NAMES=__NAMES__;let cur=localStorage.getItem('jw_char')||Object.keys(NAMES)[0];if(!NAMES[cur])cur=Object.keys(NAMES)[0];
let pos=-1,busy=false,lines=0;const L=document.getElementById('log'),S=document.getElementById('st');
function mk(){const t=document.getElementById('tabs');t.innerHTML='';for(const k in NAMES){const b=document.createElement('button');b.textContent=NAMES[k];if(k===cur)b.className='on';b.onclick=()=>{cur=k;try{localStorage.setItem('jw_char',k)}catch(e){};pos=-1;L.innerHTML='';mk()};t.appendChild(b)}}
mk();
const rxP=/^\d\d?:\d\d:\d\d\s+\d+H \d+M|^\d+H \d+M /;
function cls(s){if(/## (STEP|BOT_START|ZONE_END|AREA)/.test(s))return 'step';if(/BOT_STOP|ОШИБКА|!!!|мертв[ао]? для|Вы умерли|Вы мертвы/.test(s))return 'bad';if(/R\.I\.P|Вы получили \d+ единиц/.test(s))return 'ok';if(/^\S+\s+>> /.test(s)||/^>> /.test(s))return 'cmd';if(rxP.test(s))return 'prompt';return ''}
async function tick(){if(busy)return;busy=true;try{const r=await fetch('/api/'+cur+'?pos='+pos);const j=await r.json();pos=j.pos;
 if(j.text){const show=document.getElementById('pr').checked;const fr=document.createDocumentFragment();
  for(const s of j.text.split('\n')){if(!s.trim())continue;const c=cls(s);if(c==='prompt'&&!show)continue;const d=document.createElement('span');d.className='l '+c;d.textContent=s;fr.appendChild(d);lines++}
  L.appendChild(fr);while(L.childElementCount>3000)L.removeChild(L.firstChild);
  if(document.getElementById('fl').checked)window.scrollTo(0,document.body.scrollHeight)}
 S.textContent=NAMES[cur]+' · '+j.size+' байт · '+j.mtime}catch(e){S.textContent='нет связи'}busy=false}
document.getElementById('clr').onclick=()=>{L.innerHTML=''};setInterval(tick,1000);tick();
</script></body></html>"""


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        b = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, "text/html; charset=utf-8", PAGE.replace("__NAMES__", json.dumps({k: v[0] for k, v in CHARS.items()}, ensure_ascii=False)))
        if u.path.startswith("/api/"):
            key = u.path[5:]
            if key not in CHARS:
                return self._send(404, "text/plain", "нет такого персонажа")
            path = CHARS[key][1]
            q = urllib.parse.parse_qs(u.query); pos = int(q.get("pos", ["-1"])[0])
            try:
                size = os.path.getsize(path)
                if pos < 0 or pos > size:           # старт: последние 40 КБ (после ротации - с начала)
                    pos = max(0, size - 40000)
                with open(path, "rb") as f:
                    f.seek(pos); data = f.read(400000)
                new = pos + len(data)
                import time
                mt = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(path)))
                return self._send(200, "application/json", json.dumps({"pos": new, "size": size, "mtime": mt, "text": data.decode("cp1251", "replace")}, ensure_ascii=False))
            except OSError as e:
                return self._send(200, "application/json", json.dumps({"pos": 0, "size": 0, "mtime": "-", "text": "", "err": str(e)}))
        self._send(404, "text/plain", "404")


class T(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print("вывод жабы: http://127.0.0.1:%d/" % PORT, flush=True)
    T(("127.0.0.1", PORT), H).serve_forever()
