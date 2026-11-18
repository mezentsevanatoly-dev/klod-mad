"""Карта всех комнат из data/game.db (таблица rooms: связи из MSDP) -> data/map.html (самодостаточный файл: выбор зоны, масштаб, поиск).
Раскладка: обход в ширину по выходам N/S/E/W на сетку; вверх/вниз и переходы в другие зоны — отдельные отметки.
"""
import json
import os
import sqlite3
from collections import deque, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
D = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


def main():
    c = sqlite3.connect(DB)
    rooms, byzone = {}, defaultdict(list)
    for v, z, n, ex in c.execute("select vnum,zone,name,exits from rooms"):
        try:
            e = json.loads(ex or "{}")
        except Exception:
            e = {}
        rooms[v] = (z, n, e)
        byzone[z].append(v)
    surveyed = {r[0] for r in c.execute("select distinct zone from mob_cards")}
    mobs = defaultdict(int)
    for z, n in c.execute("select zone,count(*) from mob_cards group by zone"):
        mobs[z] = n
    out = {}
    for z, vs in byzone.items():
        pos, used, comp_x = {}, {}, 0
        for start in vs:
            if start in pos:
                continue
            ox = comp_x
            pos[start] = (ox, 0)
            used[(ox, 0)] = start
            q = deque([start])
            while q:
                a = q.popleft()
                ax, ay = pos[a]
                for d, b in rooms[a][2].items():
                    if d in D and b in rooms and rooms[b][0] == z and b not in pos:
                        p = (ax + D[d][0], ay + D[d][1])
                        while p in used:                      # клетка занята (карта не плоская): сдвиг вправо
                            p = (p[0] + 1, p[1])
                        pos[b] = p
                        used[p] = b
                        q.append(b)
            xs = [p[0] for p in pos.values()]
            comp_x = max(xs) + 3
        ms = {v: (rooms[v][1], pos[v]) for v in vs}
        edges, links = [], []
        for a in vs:
            for d, b in rooms[a][2].items():
                if b not in rooms:
                    continue
                if rooms[b][0] == z and d in D:
                    if a < b:
                        edges.append([a, b])
                elif rooms[b][0] != z:
                    links.append([a, d, rooms[b][0]])
                elif d in ("U", "D"):
                    links.append([a, d, "эта же зона"])
        out[z] = {"rooms": [[v, ms[v][0], ms[v][1][0], ms[v][1][1]] for v in vs], "edges": edges, "links": links,
                  "seen": z in surveyed, "mobs": mobs.get(z, 0)}
    html = HTML.replace("__DATA__", json.dumps(out, ensure_ascii=False))
    open(os.path.join(HERE, "data", "map.html"), "w", encoding="utf-8").write(html)
    print("зон:", len(out), "комнат:", len(rooms))


HTML = """<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Карта мира Айлины</title>
<style>
:root{--bg:#fff;--fg:#1c1c1e;--mut:#6b6b70;--line:#8a8a90;--room:#e8eef7;--seen:#cfe8d5;--link:#d97706;--brd:#c9c9cf}
@media(prefers-color-scheme:dark){:root{--bg:#15161a;--fg:#e8e8ea;--mut:#9a9aa2;--line:#6d6d76;--room:#2a3140;--seen:#2f5a3c;--link:#f59e0b;--brd:#3a3b42}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px system-ui,sans-serif}
header{display:flex;flex-wrap:wrap;gap:8px;padding:10px 16px;border-bottom:1px solid var(--brd);align-items:center}
select,input{font:inherit;padding:5px 8px;background:var(--bg);color:var(--fg);border:1px solid var(--brd);border-radius:6px}
#info{color:var(--mut);padding:6px 16px}#cv{width:100%;height:calc(100vh - 110px);display:block;touch-action:none}
.hint{color:var(--mut);font-size:12px}
</style>
<header><select id="z"></select><input id="q" placeholder="поиск комнаты"><span class="hint">колесо — масштаб, перетаскивание — сдвиг. Зелёные зоны: мобы записаны в базу</span></header>
<div id="info"></div><canvas id="cv"></canvas>
<script>
const DATA=__DATA__;const cv=document.getElementById('cv'),cx=cv.getContext('2d');
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let z,sc=22,ox=40,oy=40,hit=null,q='';
const sel=document.getElementById('z');
Object.keys(DATA).sort((a,b)=>DATA[b].mobs-DATA[a].mobs||a.localeCompare(b)).forEach(k=>{const o=document.createElement('option');o.value=k;o.textContent=(DATA[k].seen?'● ':'')+k+' ('+DATA[k].rooms.length+')';sel.appendChild(o)});
function fit(){const R=DATA[z].rooms;let a=1e9,b=-1e9,c=1e9,d=-1e9;R.forEach(r=>{a=Math.min(a,r[2]);b=Math.max(b,r[2]);c=Math.min(c,r[3]);d=Math.max(d,r[3])});
 const W=cv.clientWidth,H=cv.clientHeight;sc=Math.max(6,Math.min(40,Math.min((W-60)/(b-a+1),(H-60)/(d-c+1))));ox=30-a*sc+(W-60-(b-a+1)*sc)/2;oy=30-c*sc;}
function setZ(k){z=k;fit();q='';document.getElementById('q').value='';const m=DATA[z];
 document.getElementById('info').textContent=z+': комнат '+m.rooms.length+', связей '+m.edges.length+', выходов в другие зоны '+m.links.length+(m.seen?', мобов в базе '+m.mobs:'');draw()}
function draw(){const dpr=devicePixelRatio||1;cv.width=cv.clientWidth*dpr;cv.height=cv.clientHeight*dpr;cx.setTransform(dpr,0,0,dpr,0,0);
 const m=DATA[z],P={};m.rooms.forEach(r=>P[r[0]]=r);
 cx.strokeStyle=css('--line');cx.lineWidth=1.5;cx.beginPath();m.edges.forEach(e=>{const a=P[e[0]],b=P[e[1]];cx.moveTo(ox+a[2]*sc,oy+a[3]*sc);cx.lineTo(ox+b[2]*sc,oy+b[3]*sc)});cx.stroke();
 const s=Math.max(3,sc*0.34);
 m.rooms.forEach(r=>{const x=ox+r[2]*sc,y=oy+r[3]*sc;cx.fillStyle=m.seen?css('--seen'):css('--room');cx.strokeStyle=css('--line');
  if(q&&r[1].toLowerCase().includes(q)){cx.fillStyle='#f59e0b'}cx.fillRect(x-s,y-s,2*s,2*s);cx.strokeRect(x-s,y-s,2*s,2*s)});
 cx.fillStyle=css('--link');m.links.forEach(l=>{const a=P[l[0]];if(!a)return;const x=ox+a[2]*sc,y=oy+a[3]*sc;cx.beginPath();cx.arc(x+sc*0.3,y-sc*0.3,Math.max(2,sc*0.12),0,7);cx.fill()});
 if(hit){cx.fillStyle=css('--fg');cx.font='12px system-ui';const t=hit[1]+' ['+hit[0]+']';cx.fillText(t,Math.min(ox+hit[2]*sc+10,cv.clientWidth-t.length*6-10),oy+hit[3]*sc-10)}}
sel.onchange=()=>setZ(sel.value);document.getElementById('q').oninput=e=>{q=e.target.value.toLowerCase();draw()};
cv.onwheel=e=>{e.preventDefault();const k=e.deltaY<0?1.15:0.87,r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;ox=mx-(mx-ox)*k;oy=my-(my-oy)*k;sc*=k;draw()};
let dr=null;cv.onpointerdown=e=>{dr=[e.clientX,e.clientY,ox,oy]};addEventListener('pointerup',()=>dr=null);
cv.onpointermove=e=>{if(dr){ox=dr[2]+e.clientX-dr[0];oy=dr[3]+e.clientY-dr[1];draw();return}
 const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let b=null,bd=(sc*0.5)**2;DATA[z].rooms.forEach(v=>{const d=(ox+v[2]*sc-mx)**2+(oy+v[3]*sc-my)**2;if(d<bd){bd=d;b=v}});if(b!==hit){hit=b;draw()}};
addEventListener('resize',()=>{fit();draw()});
const first=Object.keys(DATA).sort((a,b)=>DATA[b].mobs-DATA[a].mobs)[0];sel.value=first;setZ(first);
</script></html>"""

if __name__ == "__main__":
    main()
