import os, sqlite3, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
import recon_all as R
name = "бесы"
R.say(name, "повторный обход (решётка 160012 открыта)")
res = R.run_map(name)
R.say(name, "обход:", res)
nm, dropped = R.finish_csv(name)
vmsg = R.build_tour(name, "e", "16e8nw5n3wn", "105003", "с", None)
R.say(name, vmsg, "csv", nm, "выше уровня:", dropped)
if res != "dead":
    R.go("105003")
    R.cmd("!sw " + R.inv("16e8nw5n3wn"))
open(os.path.join(R.RECON, name, f"Разведка_{name}.md"), "w", encoding="utf-8").write(
    f"# {name}: разведка Айлиной\n\n- зона «Тоннель бесов» (22–25), вход: 105003 «На дне оврага» (Тёмный лес), `область создать с`; подход от площади Элементра: 16e8nw5n3wn\n"
    f"- обход: {res}; {vmsg}\n- мобов в csv: {nm}; не в csv (выше лвл+1): {', '.join(dropped) or 'нет'}\n"
    "- в зоне темно («слишком темно» у соседних клеток): нужны инфразрение/свет; железная решётка на 160012 север открывается `открыть железная север`\n")
