import re, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
import recon_all as R
g = R.mkv.graph(R.OUTLOG)
a, b = sys.argv[1], sys.argv[2]
p = R.bfs(g, a, b)
if p is None:
    print("нет пути"); sys.exit()
s = "".join(d.lower() for d in p)
print(re.sub(r"(.)\1+", lambda m: f"{len(m.group(0))}{m.group(1)}", s), len(s))
