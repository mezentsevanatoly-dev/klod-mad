p = r"C:\Users\User\Desktop\Тадия\areas\парк_mob.csv"
import shutil; shutil.copyfile(p, p + ".bak")
rows = open(p, "rb").read().decode("cp1251").split("\r\n")
out = []
for r in rows:
    if r.startswith('"Ворон";') or r.startswith('"Ворона";'):
        continue                       # выше лвл+1 и общее описание: бот зацикливался на «Кого вы хотите ударить?»
    if r.startswith('"Бабочка";'):
        f = r.split(";")
        f[1] = '"Желтая бабочка порхает с ветки на ветку. "'
        r = ";".join(f)
    out.append(r)
open(p, "wb").write("\r\n".join(out).encode("cp1251"))
print(len(rows), "->", len(out))
