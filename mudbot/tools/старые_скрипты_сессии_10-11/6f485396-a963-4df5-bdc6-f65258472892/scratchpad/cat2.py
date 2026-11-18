import os, re, sqlite3, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
import recon_all as R

name = "геоканал3"
# начало всех прогонов по этому инстансу: идём от конца out.log назад, пока комнаты катакомб (226xxx) или вход 115042
data = open(R.OUTLOG, "rb").read()
tail_start = max(0, len(data) - 6_000_000)
chunk = data[tail_start:]
lines = chunk.split(b"\n")
pos = [0]
for l in lines:
    pos.append(pos[-1] + len(l) + 1)
rx = re.compile(r"^\[msdp\] комната (\d+) \|".encode("utf-8"))
start = len(chunk)
for i in range(len(lines) - 1, -1, -1):
    m = rx.match(lines[i])
    if m:
        v = m.group(1).decode()
        if v.startswith("226") or v == "115042":
            start = pos[i]
        else:
            break
offset = tail_start + start
R.say(name, "второй обход катакомб (двери открыты), начало прогонов с байта", offset)
res = R.run_map(name)
R.say(name, "обход:", res)
nm, dropped = R.finish_csv(name)
vmsg = R.build_tour(name, "g", "2nw", "115042", "вни", offset)
R.say(name, vmsg, "csv", nm, "выше уровня:", dropped)
if res != "dead":
    R.go("115042")
    R.cmd("!sw " + R.inv("2nw"))
open(os.path.join(R.RECON, name, f"Разведка_{name}.md"), "w", encoding="utf-8").write(
    f"# {name}: разведка Айлиной\n\n- обход: {res} (два прохода по одному инстансу)\n- {vmsg}\n"
    f"- мобов в csv: {nm}; не в csv (выше лвл+1): {', '.join(dropped) or 'нет'}\n"
    "- вход 115042 «Тупик», `область создать вниз`, подход 2nw от площади Геоланта\n"
    "- двери: 226001 запад — деревянная дверь (`отпер дверь;откр дверь`), люки на 226001, 226006 и 226025 (`откр люк`); триггеры бота "
    "открывают их только при ходьбе по ним, обход по миникарте сам не открывал\n")
