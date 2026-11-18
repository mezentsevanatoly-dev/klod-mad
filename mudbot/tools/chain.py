"""Цепочка этапов: python tools/chain.py аллея:8 канал:9 болото_часть:11 ...  (лог:стоп_уровень), каждый этап — inc_run.py."""
import subprocess
import sys
import time

for arg in sys.argv[1:]:
    name, stop = arg.rsplit(":", 1)
    t0 = time.time()
    print(f"=== этап {name} до {stop} лвл ===", flush=True)
    rc = subprocess.call([sys.executable, "-X", "utf8", "tools/inc_run.py", name, stop])
    print(f"=== {name}: код {rc}, {int(time.time() - t0) // 60} мин ===", flush=True)
    if rc != 0:
        sys.exit(rc)
