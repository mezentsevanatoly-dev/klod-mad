import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): (z, n, json.loads(e) if e.startswith("{") else {}) for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms")}
for v, (z, n, e) in R.items():
    if n == "Дорога" and z == "Дорога Геолант - Элендор" and "W" in e:
        t = e["W"]
        if t in R and R[t][1] == "Поле":
            print("Дорога", v, "-W->", t, R[t][1], R[t][2])
print("107002:", R.get("107002"))
for v in ("107001", "107005"):
    print(v, R.get(v))
