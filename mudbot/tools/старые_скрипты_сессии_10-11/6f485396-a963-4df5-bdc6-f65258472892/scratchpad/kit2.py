import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
SL = {"на голову": "голова", "на шею": "шея", "на тело": "тело", "вокруг талии": "талия", "на кисти рук": "кисти", "на руки": "руки",
      "на ноги": "ноги", "как обувь": "обувь", "на запястье": "запястье", "на палец": "палец", "на дополнительный слот": "доп"}
def slot(sl, name):
    for k, v in SL.items():
        if k in sl:
            return v
    return "плечи"
rows = c.execute("select dept,name,slot,minlvl,ac,cut,crush,pierce,stars,timer,unique_flag,special,mods,rating,cnt from ksk_items").fetchall()
out = []
for d, n, s, m, ac, cu, cr, pi, st, t, u, sp, mods, rt, cnt in rows:
    out.append((slot(s, n), m, d, n, ac, cu, st, t, "У" if u else "", cnt, rt.split(",")[1] if "," in rt else ""))
for r in sorted(out):
    print(r)
