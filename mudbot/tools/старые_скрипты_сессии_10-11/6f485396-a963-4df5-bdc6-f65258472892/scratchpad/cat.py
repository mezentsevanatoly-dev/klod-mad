import os, sqlite3, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
import recon_all as R

name = "геоканал3"
R.log_prep.prep(name, sqlite3.connect(R.DBPATH))
import json
route = json.load(open(os.path.join(R.RECON, name, name + "_route.json"), encoding="utf-8"))["steps"]
json.dump({"start": None, "steps": route}, open(os.path.join(R.ROOT, "data", "db", "routes", name + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
R.say(name, "обход в живом инстансе (вход 115042, вниз)")
offset = os.path.getsize(R.OUTLOG)
res = R.run_map(name)
R.say(name, "обход:", res)
nm, dropped = R.finish_csv(name)
vmsg = R.build_tour(name, "g", "2nw", "115042", "вни", offset)
R.say(name, vmsg, "csv", nm, "выше уровня:", dropped)
if res != "dead":
    R.go("115042")
    R.cmd("!sw " + R.inv("2nw"))
open(os.path.join(R.RECON, name, f"Разведка_{name}.md"), "w", encoding="utf-8").write(
    f"# {name}: разведка Айлиной\n\n- обход: {res}\n- {vmsg}\n- мобов в csv: {nm}; не в csv (выше лвл+1): {', '.join(dropped) or 'нет'}\n"
    "- вход 115042 «Тупик», `область создать вниз`, подход 2nw от площади Геоланта; люк на 226001 открывается шагом `вниз` (триггер)\n")
