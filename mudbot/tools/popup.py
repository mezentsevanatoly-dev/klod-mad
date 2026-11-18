# -*- coding: utf-8 -*-
"""Всплывающее окно поверх всех окон: pythonw tools/popup.py "Заголовок" "Текст (\\n = новая строка)" """
import sys
import tkinter as tk

title = sys.argv[1] if len(sys.argv) > 1 else "Claude"
text = (sys.argv[2] if len(sys.argv) > 2 else "").replace("\\n", "\n")
r = tk.Tk()
r.title(title)
r.geometry("640x360+120+120")
r.attributes("-topmost", True)
t = tk.Text(r, font=("Segoe UI", 11), wrap="word", bg="#fffbe6")
t.pack(fill="both", expand=True, padx=8, pady=8)
t.insert("end", text)
t.configure(state="disabled")
tk.Button(r, text="Закрыть", command=r.destroy, font=("Segoe UI", 10)).pack(pady=(0, 8))
r.mainloop()
