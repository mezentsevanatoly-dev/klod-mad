import os, sys, time
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
import jmc_watch as jw
jw.STALL_SEC = 1
w = jw.Watch()
lines = ["12:00:01 ## BOT_START zone=школа steps=40", "12:00:02 ## STEP 0 vn=100076 cmd=юг", "12:00:03 Мышь мертва. R.I.P.", "12:00:03 Вы не можете идти в этом направлении...", "12:00:04 ## STEP 1 vn=100077 cmd=север"]
with open(os.environ["JMC_WATCH_LOG"], "ab") as f:
    for l in lines: f.write((l + "\r\n").encode("cp1251"))
w.feed(); time.sleep(1.5); w.tick()
with open(os.environ["JMC_WATCH_LOG"], "ab") as f:
    f.write("12:00:09 ## ZONE_END zone=школа steps=40\r\n".encode("cp1251"))
w.feed()
print(w.status())
