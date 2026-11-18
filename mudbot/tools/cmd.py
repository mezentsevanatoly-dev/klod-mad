"""Отправить команду в JMC Айлины и показать ответ игры: python -X utf8 tools/cmd.py "<команда>" [секунд=3]"""
import os, sys, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc
s = jmc.log_size()
jmc.type_line(sys.argv[1], force=True)
time.sleep(float(sys.argv[2]) if len(sys.argv) > 2 else 3)
print("\n".join(l[9:] for l in jmc.read_log(s) if l.strip() and "## WHERE" not in l)[-2500:])
