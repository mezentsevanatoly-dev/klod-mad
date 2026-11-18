# -*- coding: utf-8 -*-
"""Окно саммари прокачки: хвост tools/inc_supervisor.log + уровень/зона. Запуск: pythonw tools/inc_window.py"""
import os, tkinter as tk
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inc_supervisor.log")
r = tk.Tk(); r.title("Прокачка Тадии (варвар 1-21) — саммари"); r.geometry("760x420+40+40"); r.attributes("-topmost", True)
t = tk.Text(r, font=("Consolas", 10), bg="#101418", fg="#d8e0e8", wrap="word"); t.pack(fill="both", expand=True)
def tick():
    try:
        d = open(LOG, encoding="utf-8", errors="replace").read().splitlines()[-200:]
    except OSError:
        d = ["лог надсмотрщика ещё не создан"]
    t.delete("1.0", "end"); t.insert("end", "\n".join(d)); t.see("end"); r.after(3000, tick)
tick(); r.mainloop()