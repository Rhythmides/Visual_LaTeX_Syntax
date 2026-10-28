#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual LaTeX Syntax
A lightweight, visual-first formula editor built with Python's standard-library Tkinter.
Export target: Markdown math (LaTeX) and mhchem's \\ce{} chemistry syntax.
"""
import json
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Visual LaTeX Syntax"
BASE_SIZE = 24  # 基准字号
FONT_FAMILY = "Times New Roman"
PLACEHOLDER = "□"

GREEK = [
    ("α", r"\alpha"), ("β", r"\beta"), ("γ", r"\gamma"), ("δ", r"\delta"),
    ("ε", r"\varepsilon"), ("ζ", r"\zeta"), ("η", r"\eta"), ("θ", r"\theta"),
    ("ι", r"\iota"), ("κ", r"\kappa"), ("λ", r"\lambda"), ("μ", r"\mu"),
    ("ν", r"\nu"), ("ξ", r"\xi"), ("π", r"\pi"), ("ρ", r"\rho"),
    ("σ", r"\sigma"), ("τ", r"\tau"), ("φ", r"\varphi"), ("χ", r"\chi"),
    ("ψ", r"\psi"), ("ω", r"\omega"), ("Γ", r"\Gamma"), ("Δ", r"\Delta"),
    ("Θ", r"\Theta"), ("Λ", r"\Lambda"), ("Ξ", r"\Xi"), ("Π", r"\Pi"),
    ("Σ", r"\Sigma"), ("Φ", r"\Phi"), ("Ψ", r"\Psi"), ("Ω", r"\Omega"),
]
SYMBOLS = [
    ("+", "+"), ("−", "-"), ("=", "="), ("×", r"\times"), ("÷", r"\div"),
    ("±", r"\pm"), ("∓", r"\mp"), ("·", r"\cdot"), ("⋅", r"\cdot"),
    ("<", "<"), (">", ">"), ("≤", r"\leq"), ("≥", r"\geq"), ("≠", r"\neq"),
    ("≈", r"\approx"), ("≡", r"\equiv"), ("∝", r"\propto"), ("∞", r"\infty"),
    ("∠", r"\angle"), ("°", r"^\circ"), ("∴", r"\therefore"), ("∵", r"\because"),
    ("→", r"\rightarrow"), ("←", r"\leftarrow"), ("↔", r"\leftrightarrow"),
    ("⇒", r"\Rightarrow"), ("⇔", r"\Leftrightarrow"), ("∈", r"\in"),
    ("∉", r"\notin"), ("⊂", r"\subset"), ("⊆", r"\subseteq"), ("∪", r"\cup"),
    ("∩", r"\cap"), ("∅", r"\emptyset"), ("∀", r"\forall"), ("∃", r"\exists"),
    ("¬", r"\neg"), ("∧", r"\land"), ("∨", r"\lor"), ("⊥", r"\perp"),
    ("∥", r"\parallel"), ("∇", r"\nabla"), ("∂", r"\partial"), ("ℝ", r"\mathbb{R}"),
    ("ℤ", r"\mathbb{Z}"), ("ℕ", r"\mathbb{N}"), ("ℚ", r"\mathbb{Q}"), ("ℂ", r"\mathbb{C}"),
]
CHEM = [
    ("反应箭头", "→"), ("可逆反应", "⇌"), ("沉淀", "↓"), ("气体", "↑"),
    ("加热 Δ", "Δ"), ("催化剂", "催化剂"), ("溶液 (aq)", "(aq)"),
    ("固体 (s)", "(s)"), ("液体 (l)", "(l)"), ("气体 (g)", "(g)"),
    ("电荷 +", "^+"), ("电荷 −", "^-"), ("电子 e⁻", "e^-"),
    ("水 H₂O", "H2O"), ("氢离子", "H^+"), ("氢氧根", "OH^-"),
    ("硫酸根", "SO4^2-"), ("碳酸根", "CO3^2-"), ("铵根", "NH4^+"),
    ("钠离子", "Na^+"), ("氯离子", "Cl^-"),
]
STRUCTURES = [
    ("分数 □/□", "frac"), ("根号 √□", "sqrt"), ("上标 □^□", "sup"), ("下标 □_□", "sub"),
    ("上下标 □_□□^□", "subsup"), ("括号 (□)", "paren"), ("绝对值 |□|", "abs"),
    ("向量 →□", "vec"), ("上划线 ¯□", "bar"), ("求和 ∑", "sum"), ("积分 ∫", "int"),
    ("极限 lim", "lim"), ("矩阵 2×2", "matrix"), ("分段 {□", "cases"),
    ("换行 ⏎", "newline"), ("对齐 &", "align")
]
FUNCTIONS = ["sin", "cos", "tan", "arcsin", "arccos", "ln", "log", "exp", "lim", "max", "min", "det"]

def row():
    return {"t": "row", "kids": []}

def txt(value):
    return {"t": "txt", "v": value}

def escape_text(s):
    out = []
    for c in s:
        if c in r"{}$#_^%":
            out.append("\\" + c)
        elif c == "~":
            out.append(r"\textasciitilde{}")
        else:
            out.append(c)
    return "".join(out)

class VisualLatexApp:
    def __init__(self, root_window):
        self.win = root_window
        self.win.title(APP_NAME)
        self.win.geometry("1120x760")
        self.win.minsize(820, 580)
        self.root = row()
        self.active = self.root
        self.cursor = 0
        
        self.parent_map = {}
        self.undo_stack = []
        self.chem_mode = False
        self.hit_boxes = []

        self._build_ui()
        self._bind_keys()
        self.render()
        self.canvas.focus_set()

    def _build_ui(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        top = ttk.Frame(self.win, padding=(12, 10))
        top.pack(fill="x")
        ttk.Label(top, text=APP_NAME, font=("TkDefaultFont", 16, "bold")).pack(side="left")
        ttk.Label(top, text="在排版后的公式中编辑 · 导出 Markdown / LaTeX", foreground="#666").pack(side="left", padx=18)
        ttk.Button(top, text="撤销一步", command=self.undo).pack(side="right")
        ttk.Button(top, text="清空", command=self.clear).pack(side="right", padx=6)

        self.tabs = ttk.Notebook(self.win)
        self.tabs.pack(fill="x", padx=10, pady=(0, 6))
        self.tool_frame = ttk.Frame(self.win, padding=(10, 7))
        self.tool_frame.pack(fill="x")
        self._make_tab("结构", [x[0] for x in STRUCTURES], self._structure_click)
        self._make_tab("拉丁字母", list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"), self.insert_text)
        self._make_tab("希腊字母", [x[0] for x in GREEK], self._greek_click)
        self._make_tab("数学符号", [x[0] for x in SYMBOLS], self._symbol_click)
        self._make_tab("函数", FUNCTIONS, self._function_click)
        self._make_tab("化学", [x[0] for x in CHEM], self._chem_click)
        self._make_tab("数字/标点", list("0123456789") + [".", ",", ";", ":", "(", ")", "[", "]", "{", "}", "=", "+", "-", "/"], self.insert_text)
        
        helpbar = ttk.Frame(self.win, padding=(12, 0, 12, 6))
        helpbar.pack(fill="x")
        ttk.Label(helpbar, text="键盘：字符输入 · 回车换行 · ←/→ 内部/跨越移动 · ↑/↓ 视觉位置跳转 · Backspace 删除 · Tab 切换空位",
                  foreground="#555").pack(side="left")
                  
        self.canvas = tk.Canvas(self.win, background="white", highlightthickness=1, highlightbackground="#ddd")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.canvas.bind("<Button-1>", self._canvas_click)
        self.canvas.bind("<Configure>", lambda e: self.render())

        # 初始化画布后再加载工具
        self._show_tools(0)

        bottom = ttk.Frame(self.win, padding=(10, 0, 10, 10))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="复制 Markdown", command=self.copy_markdown).pack(side="right")
        ttk.Button(bottom, text="导出 .md", command=self.export_md).pack(side="right", padx=6)
        ttk.Button(bottom, text="查看/编辑输出", command=self.show_output).pack(side="right", padx=6)
        self.status = ttk.Label(bottom, text="就绪", foreground="#666")
        self.status.pack(side="left")

    def _make_tab(self, name, labels, callback):
        tab = ttk.Frame(self.tabs, padding=5)
        self.tabs.add(tab, text=name)
        tab._labels = labels
        tab._callback = callback

    def _show_tools(self, tab_index):
        self.chem_mode = (tab_index == 5)
        tab = self.tabs.nametowidget(self.tabs.tabs()[tab_index])
        for child in tab.winfo_children():
            child.destroy()
        labels = tab._labels
        cols = 12
        for i, label in enumerate(labels):
            btn = ttk.Button(tab, text=label, width=max(4, min(12, len(label)+1)),
                             command=lambda x=label, cb=tab._callback: cb(x))
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2, sticky="ew")
        for c in range(cols):
            tab.columnconfigure(c, weight=1)
        if hasattr(self, 'canvas'):
            self.canvas.focus_set()

    def _bind_keys(self):
        self.win.bind("<Key>", self._key)
        self.win.bind("<Left>", lambda e: self.move_horizontal(-1))
        self.win.bind("<Right>", lambda e: self.move_horizontal(1))
        self.win.bind("<Up>", lambda e: self.move_vertical(-1))
        self.win.bind("<Down>", lambda e: self.move_vertical(1))
        self.win.bind("<BackSpace>", self._backspace)
        self.win.bind("<Delete>", self._delete)
        self.win.bind("<Tab>", self._tab_next)
        self.win.bind("<Control-z>", lambda e: self.undo())
        self.win.bind("<Command-z>", lambda e: self.undo())

    def _snapshot(self):
        self.undo_stack.append((json.loads(json.dumps(self.root)), self._active_path()))
        if len(self.undo_stack) > 80:
            self.undo_stack.pop(0)

    def _active_path(self):
        return self._find_row_path(self.root, self.active, []) or []

    def _find_row_path(self, r, target, path):
        if r is target: return path
        for i, n in enumerate(r["kids"]):
            for key in ("num","den","body","base","exp","sub","sup","arg"):
                child = n.get(key)
                if isinstance(child, dict) and child.get("t") == "row":
                    result = self._find_row_path(child, target, path + [("kid", i, key)])
                    if result is not None: return result
            if n["t"] == "matrix":
                for ri, rr in enumerate(n["rows"]):
                    for ci, cell in enumerate(rr):
                        result = self._find_row_path(cell, target, path + [("kid",i,"rows",ri,ci)])
                        if result is not None: return result
            if n["t"] == "cases":
                for ri, cell in enumerate(n["rows"]):
                    result = self._find_row_path(cell, target, path + [("kid",i,"rows",ri)])
                    if result is not None: return result
        return None

    def _resolve_path(self, root, path):
        cur = root
        for step in path:
            if len(step) == 3:
                _, i, key = step; cur = cur["kids"][i][key]
            else:
                _, i, key, *rest = step
                n = cur["kids"][i]
                cur = n[key]
                for idx in rest: cur = cur[idx]
        return cur

    def undo(self):
        if not self.undo_stack:
            self.status.config(text="没有可撤销的操作")
            return
        old_root, path = self.undo_stack.pop()
        self.root = old_root
        try: self.active = self._resolve_path(self.root, path)
        except Exception: self.active = self.root
        self.cursor = len(self.active["kids"])
        self.render()
        self.canvas.focus_set()

    def _set_active(self, r, pos=None):
        self.active = r
        self.cursor = len(r["kids"]) if pos is None else max(0, min(pos, len(r["kids"])))
        self.render()
        self.canvas.focus_set()

    def _insert_node(self, n, target=None):
        self._snapshot()
        target = target or self.active
        target["kids"].insert(self.cursor, n)
        self.cursor += 1
        self.status.config(text="已插入结构")
        self.render()
        self.canvas.focus_set()

    def insert_text(self, value):
        if not value: return
        self._snapshot()
        if self.chem_mode:
            self.active["kids"].insert(self.cursor, {"t":"txt", "v":str(value), "raw":True})
        else:
            self.active["kids"].insert(self.cursor, txt(str(value)))
        self.cursor += 1
        self.render()
        self.canvas.focus_set()

    def _structure_click(self, label):
        key = dict(STRUCTURES).get(label)
        if not key: return
        self._snapshot()
        def newrow(): return row()
        if key == "newline":
            self._insert_node({"t": "newline"})
        elif key == "align":
            self.active["kids"].insert(self.cursor, {"t": "txt", "v": "&", "raw": True})
            self.cursor += 1
            self.render()
        elif key == "frac":
            n = {"t":"frac", "num":newrow(), "den":newrow()}
            self._insert_node(n); self._set_active(n["num"], 0)
        elif key == "sqrt":
            n = {"t":"sqrt", "body":newrow()}
            self._insert_node(n); self._set_active(n["body"], 0)
        elif key in ("sup","sub","subsup"):
            base = row()
            if self.cursor > 0:
                base["kids"].append(self.active["kids"].pop(self.cursor-1))
                self.cursor -= 1
            if key == "sup": n={"t":"sup","base":base,"exp":newrow()}; target=n["exp"]
            elif key == "sub": n={"t":"sub","base":base,"sub":newrow()}; target=n["sub"]
            else: n={"t":"subsup","base":base,"sub":newrow(),"sup":newrow()}; target=n["sub"]
            self._insert_node(n); self._set_active(target, 0)
        elif key in ("paren","abs","vec","bar"):
            body = newrow()
            n={"t":key,"body":body}
            self._insert_node(n); self._set_active(body,0)
        elif key in ("sum","int","lim"):
            n={"t":key,"sub":newrow(),"sup":newrow()}
            self._insert_node(n); self._set_active(n["sub"],0)
        elif key == "matrix":
            cells=[[newrow(),newrow()],[newrow(),newrow()]]
            n={"t":"matrix","rows":cells}
            self._insert_node(n); self._set_active(cells[0][0],0)
        elif key == "cases":
            cells=[newrow(),newrow()]
            n={"t":"cases","rows":cells}
            self._insert_node(n); self._set_active(cells[0],0)
        self.status.config(text=f"已插入：{label}")
        self.canvas.focus_set()

    def _greek_click(self, label):
        pair = next((x for x in GREEK if x[0] == label), None)
        if pair: self.insert_text(pair[0])

    def _symbol_click(self, label):
        pair = next((x for x in SYMBOLS if x[0] == label), None)
        if pair:
            self._snapshot()
            self.active["kids"].insert(self.cursor, {"t":"symbol","v":pair[0],"latex":pair[1]})
            self.cursor += 1
            self.render()
            self.canvas.focus_set()

    def _function_click(self, label):
        self._snapshot()
        n={"t":"func","name":label,"arg":row()}
        self._insert_node(n); self._set_active(n["arg"],0)

    def _chem_click(self, label):
        entry = next((x for x in CHEM if x[0] == label), None)
        if not entry: return
        self.chem_mode = True
        self._snapshot()
        value = entry[1]
        if not self.active.get("chem_row"):
            body = row()
            body["chem_row"] = True
            chem_node = {"t":"chem", "body":body}
            self.active["kids"].insert(self.cursor, chem_node)
            self.cursor += 1
            self.active = body
            self.cursor = 0
        self.active["kids"].insert(self.cursor, {"t":"txt","v":value,"raw":True})
        self.cursor += 1
        self.status.config(text="化学输入模式：内容将导出到 \\ce{...}。")
        self.render()
        self.canvas.focus_set()

    def _key(self, event):
        if event.keysym == "Return":
            self._structure_click("换行 ⏎")
            return "break"
        if event.keysym in ("Left","Right","Up","Down","BackSpace","Delete","Tab","Escape"):
            return
        if event.state & 0x4: return
        if event.char and event.char.isprintable() and event.char not in ("\r","\t"):
            self.insert_text(event.char)

    def _build_parent_map(self):
        self.parent_map = {}
        def rec(r):
            for i, n in enumerate(r["kids"]):
                for k in ("num","den","body","base","exp","sub","sup","arg"):
                    if isinstance(n.get(k), dict) and n[k].get("t") == "row":
                        self.parent_map[id(n[k])] = (r, i, k)
                        rec(n[k])
                if n["t"] == "matrix":
                    for ri, rr in enumerate(n["rows"]):
                        for ci, cell in enumerate(rr):
                            self.parent_map[id(cell)] = (r, i, ("matrix", ri, ci))
                            rec(cell)
                if n["t"] == "cases":
                    for ri, cell in enumerate(n["rows"]):
                        self.parent_map[id(cell)] = (r, i, ("cases", ri))
                        rec(cell)
        rec(self.root)

    def move_horizontal(self, delta):
        new_pos = self.cursor + delta
        if new_pos < 0:
            if id(self.active) in self.parent_map:
                p_row, p_idx, p_key = self.parent_map[id(self.active)]
                self.active = p_row; self.cursor = p_idx
            else: self.cursor = 0
            self.render(); return
        elif new_pos > len(self.active["kids"]):
            if id(self.active) in self.parent_map:
                p_row, p_idx, p_key = self.parent_map[id(self.active)]
                self.active = p_row; self.cursor = p_idx + 1
            else: self.cursor = len(self.active["kids"])
            self.render(); return
        self.cursor = new_pos
        self.render()

    def _all_edit_rows(self):
        result = []
        def rec(r):
            result.append(r)
            for n in r["kids"]:
                for k in ("num","den","body","base","exp","sub","sup","arg"):
                    if isinstance(n.get(k), dict) and n[k].get("t") == "row": rec(n[k])
                if n["t"] == "matrix":
                    for rr in n["rows"]:
                        for c in rr: rec(c)
                if n["t"] == "cases":
                    for c in n["rows"]: rec(c)
        rec(self.root)
        return result

    def move_vertical(self, delta):
        rows = self._all_edit_rows()
        try: idx = next(i for i, r in enumerate(rows) if r is self.active)
        except StopIteration: return
        new_idx = max(0, min(len(rows)-1, idx + delta))
        self._set_active(rows[new_idx], min(self.cursor, len(rows[new_idx]["kids"])))

    def _tab_next(self, event=None):
        rows = self._all_edit_rows()
        try: idx = next(i for i, r in enumerate(rows) if r is self.active)
        except StopIteration: idx = -1
        if rows: self._set_active(rows[(idx+1) % len(rows)], 0)
        return "break"

    def _backspace(self, event=None):
        if self.cursor > 0:
            self._snapshot()
            self.active["kids"].pop(self.cursor-1)
            self.cursor -= 1
        elif self.active is not self.root:
            if id(self.active) in self.parent_map:
                p_row, p_idx, p_key = self.parent_map[id(self.active)]
                # 如果是空的，且退格，直接删除父结构并跳出
                if not self.active["kids"]:
                    p_row["kids"].pop(p_idx)
                self.active = p_row; self.cursor = p_idx
        self.render()
        self.canvas.focus_set()
        return "break"

    def _delete(self, event=None):
        if self.cursor < len(self.active["kids"]):
            self._snapshot()
            self.active["kids"].pop(self.cursor)
        self.render()
        self.canvas.focus_set()
        return "break"

    def clear(self):
        if messagebox.askyesno("清空公式", "确定清空当前公式吗？"):
            self._snapshot()
            self.root = row(); self.active = self.root; self.cursor = 0; self.chem_mode = False
            self.render()
            self.canvas.focus_set()

    # ------------------ 排版与渲染引擎 ------------------
    
    def _get_font(self, size):
        return tkfont.Font(family=FONT_FAMILY, size=max(12, int(size)))

    def layout_node(self, n, size):
        font = self._get_font(size)
        t = n["t"]
        
        if t == "newline":
            return 0, font.metrics("ascent"), font.metrics("descent")
        if t in ("txt", "symbol"):
            return font.measure(n["v"]), font.metrics("ascent"), font.metrics("descent")
        if t == "frac":
            sub_size = size * 0.75
            w1, a1, d1 = self.layout_row(n["num"], sub_size)
            w2, a2, d2 = self.layout_row(n["den"], sub_size)
            axis = size * 0.25 
            gap = size * 0.15
            width = max(w1, w2) + size * 0.4
            ascent = a1 + d1 + axis + gap
            descent = a2 + d2 + gap - axis
            return width, ascent, descent
        if t == "sqrt":
            w, a, d = self.layout_row(n["body"], size)
            return w + size * 1.2, max(a, size * 0.8), max(d, size * 0.2)
        if t in ("sup", "sub", "subsup"):
            sub_size = size * 0.7
            bw, ba, bd = self.layout_row(n["base"], size)
            ew, ea, ed = (0, 0, 0)
            sw, sa, sd = (0, 0, 0)
            if n.get("exp"): ew, ea, ed = self.layout_row(n["exp"], sub_size)
            if n.get("sub"): sw, sa, sd = self.layout_row(n["sub"], sub_size)
            width = bw + max(ew, sw)
            ascent = max(ba, ea + size * 0.4)
            descent = max(bd, sd + size * 0.2)
            return width, ascent, descent
        if t in ("paren", "abs", "vec", "bar"):
            w, a, d = self.layout_row(n["body"], size)
            return w + size * 0.8, a + size * 0.2, d + size * 0.2
        if t in ("sum", "int", "lim"):
            sub_size = size * 0.7
            sym_w = font.measure({"sum":"∑", "int":"∫", "lim":"lim"}[t]) * 1.2
            w1, a1, d1 = self.layout_row(n["sub"], sub_size)
            w2, a2, d2 = self.layout_row(n["sup"], sub_size)
            ascent = size * 1.2 + a2 + d2
            descent = size * 0.8 + a1 + d1
            return sym_w + max(w1, w2), ascent, descent
        if t == "func":
            w, a, d = self.layout_row(n["arg"], size)
            return font.measure(n["name"]) + w + font.measure("(") + font.measure(")"), max(a, font.metrics("ascent")), max(d, font.metrics("descent"))
        if t == "chem":
            w, a, d = self.layout_row(n["body"], size)
            return w + size * 1.5, a, d
        if t == "matrix":
            colw = [0, 0]; rowh = [0, 0]
            for ri, rr in enumerate(n["rows"]):
                for ci, cell in enumerate(rr):
                    w, a, d = self.layout_row(cell, size)
                    colw[ci] = max(colw[ci], w)
                    rowh[ri] = max(rowh[ri], a + d)
            width = sum(colw) + size
            height = sum(rowh) + size * 0.5
            return width, height * 0.6, height * 0.4
        if t == "cases":
            max_w = 0; total_h = 0
            for rr in n["rows"]:
                w, a, d = self.layout_row(rr, size)
                max_w = max(max_w, w)
                total_h += a + d + size * 0.5
            return max_w + size * 1.5, total_h / 2, total_h / 2
        return 0, 0, 0

    def layout_row(self, r, size):
        if not r["kids"]:
            font = self._get_font(size)
            return font.measure(PLACEHOLDER), font.metrics("ascent"), font.metrics("descent")
        max_w = 0; total_a = 0; total_d = 0
        cur_w = 0; cur_a = 0; cur_d = 0
        for n in r["kids"]:
            if n["t"] == "newline":
                max_w = max(max_w, cur_w)
                total_a += cur_a + cur_d + size * 0.8
                cur_w = 0; cur_a = 0; cur_d = 0
                continue
            w, a, d = self.layout_node(n, size)
            cur_w += w + size * 0.15
            cur_a = max(cur_a, a)
            cur_d = max(cur_d, d)
        if cur_w == 0: 
            font = self._get_font(size)
            cur_w = font.measure(PLACEHOLDER)
            cur_a = font.metrics("ascent")
            cur_d = font.metrics("descent")
        max_w = max(max_w, cur_w - size * 0.15)
        total_a += cur_a
        total_d = max(total_d, cur_d)
        return max(10, max_w), total_a, total_d

    def render(self):
        if not hasattr(self, "canvas"): return
        self.canvas.delete("all")
        self.hit_boxes = []
        self._build_parent_map()
        
        w = max(300, self.canvas.winfo_width())
        h = max(120, self.canvas.winfo_height())
        
        tw, ta, td = self.layout_row(self.root, BASE_SIZE)
        th = ta + td
        
        x0 = max(22, (w - tw) / 2)
        y0 = max(22, (h - th) / 2) + ta
        
        self.draw_row(self.root, x0, y0, BASE_SIZE)
        
        if not self.root["kids"]:
            self.canvas.create_text(w/2, h/2-22, text="在这里编辑公式", fill="#888", font=("TkDefaultFont", 14))
            self.canvas.create_text(w/2, h/2+10, text="点击下方结构按钮，或直接使用键盘输入", fill="#aaa", font=("TkDefaultFont", 10))
        self.canvas.create_text(12, 12, anchor="nw", text="公式编辑区", fill="#999", font=("TkDefaultFont", 9))
        self.status.config(text=f"当前编辑位置：{'主公式' if self.active is self.root else '结构内部'}    ·    {len(self.root['kids'])} 个顶层元素")

    def draw_row(self, r, x, baseline, size):
        if not r["kids"]:
            font = self._get_font(size)
            pw = font.measure(PLACEHOLDER)
            ph_a, ph_d = font.metrics("ascent"), font.metrics("descent")
            color = "#1d5fd1" if r is self.active else "#bbbbbb"
            
            if r is self.active:
                self.canvas.create_rectangle(x-2, baseline-ph_a-2, x+pw+2, baseline+ph_d+2, outline="#d0dcf0", fill="#f4f8ff", width=1)
                self.canvas.create_line(x, baseline-ph_a/2, x, baseline+ph_d/2, fill="#1d5fd1", width=2)
                
            self.canvas.create_text(x + pw/2, baseline - (ph_a - ph_d)/2, text=PLACEHOLDER, font=font, fill=color)
            self.hit_boxes.append((x, baseline-ph_a, x+pw, baseline+ph_d, r, 0))
            return

        # 预计算每行的高度
        line_metrics = []
        cur_a = 0; cur_d = 0
        has_content = False
        for n in r["kids"]:
            if n["t"] == "newline":
                line_metrics.append((cur_a, cur_d))
                cur_a = 0; cur_d = 0
                has_content = False
            else:
                nw, na, nd = self.layout_node(n, size)
                cur_a = max(cur_a, na)
                cur_d = max(cur_d, nd)
                has_content = True
        if not has_content:
            font = self._get_font(size)
            cur_a = font.metrics("ascent")
            cur_d = font.metrics("descent")
        line_metrics.append((cur_a, cur_d))

        if r is self.active:
            tw, ta, td = self.layout_row(r, size)
            self.canvas.create_rectangle(x-4, baseline-ta-4, x+tw+4, baseline+td+4, outline="#d0dcf0", fill="#f4f8ff", width=1)

        cx = x
        cy_base = baseline
        line_idx = 0
        
        for i, n in enumerate(r["kids"]):
            if n["t"] == "newline":
                font = self._get_font(size * 0.6)
                self.canvas.create_text(cx + 4, cy_base - 4, text="↵", font=font, fill="#ccc")
                if r is self.active and self.cursor == i:
                    self.canvas.create_line(cx, cy_base-line_metrics[line_idx][0]/2, cx, cy_base+line_metrics[line_idx][1]/2, fill="#1d5fd1", width=2)
                
                cy_base += line_metrics[line_idx][0] + line_metrics[line_idx][1] + size * 0.8
                cx = x
                line_idx += 1
                
                # 如果下一行是空的（到了结尾，或者下一个又是换行），画占位符
                if i == len(r["kids"]) - 1 or r["kids"][i+1]["t"] == "newline":
                    font = self._get_font(size)
                    pw = font.measure(PLACEHOLDER)
                    pa, pd = font.metrics("ascent"), font.metrics("descent")
                    color = "#1d5fd1" if r is self.active and self.cursor == i+1 else "#bbbbbb"
                    self.canvas.create_text(x + pw/2, cy_base - (pa - pd)/2, text=PLACEHOLDER, font=font, fill=color)
                    self.hit_boxes.append((x, cy_base-pa, x+pw, cy_base+pd, r, i+1))
                    if r is self.active and self.cursor == i+1:
                        self.canvas.create_line(x, cy_base-pa/2, x, cy_base+pd/2, fill="#1d5fd1", width=2)
                continue
                
            nw, na, nd = self.layout_node(n, size)
            self.draw_node(n, cx, cy_base, size)
            
            if r is self.active and self.cursor == i + 1:
                self.canvas.create_line(cx + nw + size*0.075, cy_base - na/2 - 4, cx + nw + size*0.075, cy_base + nd/2 + 4, fill="#1d5fd1", width=2)
                
            self.hit_boxes.append((cx, cy_base-na, cx+nw, cy_base+nd, r, i+1))
            cx += nw + size * 0.15
            
        if r is self.active and self.cursor == 0:
            self.canvas.create_line(x, cy_base - line_metrics[0][0]/2, x, cy_base + line_metrics[0][1]/2, fill="#1d5fd1", width=2)

    def draw_node(self, n, x, baseline, size):
        font = self._get_font(size)
        t = n["t"]
        
        if t in ("txt", "symbol"):
            w = font.measure(n["v"])
            a, d = font.metrics("ascent"), font.metrics("descent")
            self.hit_boxes.append((x, baseline-a, x+w, baseline+d, None, None))
            self.canvas.create_text(x + w/2, baseline - (a-d)/2, text=n["v"], font=font, fill="#111")
            
        elif t == "frac":
            sub_size = size * 0.75
            w1, a1, d1 = self.layout_row(n["num"], sub_size)
            w2, a2, d2 = self.layout_row(n["den"], sub_size)
            cw = max(w1, w2) + size * 0.4
            axis = size * 0.25
            gap = size * 0.15
            
            line_y = baseline - axis
            self.canvas.create_line(x, line_y, x + cw, line_y, fill="#111", width=max(1, int(size/16)))
            
            num_base = line_y - gap - d1
            den_base = line_y + gap + a2
            
            self.draw_row(n["num"], x + (cw-w1)/2, num_base, sub_size)
            self.draw_row(n["den"], x + (cw-w2)/2, den_base, sub_size)
            
        elif t == "sqrt":
            w, a, d = self.layout_row(n["body"], size)
            h = a + d + size * 0.2
            top = baseline - a - size * 0.1
            
            path = [
                x, baseline,
                x + size*0.3, baseline - size*0.2,
                x + size*0.5, top + h*0.2, 
                x + size*0.7, top,
                x + w + size*1.2, top
            ]
            self.canvas.create_line(path, fill="#111", width=max(1, int(size/12)), joinstyle="miter")
            self.canvas.create_line(x + size*0.7, top, x + w + size*1.2, top, fill="#111", width=max(1, int(size/16)))
            
            self.draw_row(n["body"], x + size*0.8, baseline, size)
            
        elif t in ("sup", "sub", "subsup"):
            sub_size = size * 0.7
            bw, ba, bd = self.layout_row(n["base"], size)
            self.draw_row(n["base"], x, baseline, size)
            
            if n.get("exp"):
                ew, ea, ed = self.layout_row(n["exp"], sub_size)
                exp_base = baseline - ba + ea - size * 0.1
                self.draw_row(n["exp"], x + bw + size*0.05, exp_base, sub_size)
            if n.get("sub"):
                sw, sa, sd = self.layout_row(n["sub"], sub_size)
                sub_base = baseline + size * 0.2 + sa
                self.draw_row(n["sub"], x + bw + size*0.05, sub_base, sub_size)
                
        elif t in ("paren", "abs", "vec", "bar"):
            w, a, d = self.layout_row(n["body"], size)
            h = a + d
            if t == "paren":
                self.canvas.create_text(x + size*0.2, baseline - a + h/2, text="(", font=(FONT_FAMILY, int((h/size)*size*0.9)), fill="#111")
                self.draw_row(n["body"], x + size*0.5, baseline, size)
                self.canvas.create_text(x + w + size*0.5, baseline - a + h/2, text=")", font=(FONT_FAMILY, int((h/size)*size*0.9)), fill="#111")
            elif t == "abs":
                self.canvas.create_line(x + 4, baseline - a, x + 4, baseline + d, fill="#111", width=1.5)
                self.draw_row(n["body"], x + size*0.4, baseline, size)
                self.canvas.create_line(x + w + size*0.2, baseline - a, x + w + size*0.2, baseline + d, fill="#111", width=1.5)
            elif t == "vec":
                self.draw_row(n["body"], x + size*0.1, baseline, size)
                self.canvas.create_line(x + size*0.1, baseline - a - size*0.3, x + w, baseline - a - size*0.3, arrow="last", fill="#111", width=1.2)
            else:
                self.draw_row(n["body"], x + size*0.1, baseline, size)
                self.canvas.create_line(x, baseline - a - size*0.2, x + w + size*0.2, baseline - a - size*0.2, fill="#111", width=1.2)
                
        elif t in ("sum", "int", "lim"):
            sub_size = size * 0.7
            sym = {"sum":"∑", "int":"∫", "lim":"lim"}[t]
            sw = font.measure(sym) * 1.2
            self.canvas.create_text(x + sw/2, baseline - size*0.4, text=sym, font=(FONT_FAMILY, int(size*1.2)), fill="#111")
            
            if n.get("sup"):
                ew, ea, ed = self.layout_row(n["sup"], sub_size)
                exp_base = baseline - size*1.2
                self.draw_row(n["sup"], x + sw, exp_base, sub_size)
            if n.get("sub"):
                sw_, sa, sd = self.layout_row(n["sub"], sub_size)
                sub_base = baseline + size*0.2 + sa
                self.draw_row(n["sub"], x + sw, sub_base, sub_size)
                
        elif t == "func":
            name = n["name"]
            tw = font.measure(name)
            self.canvas.create_text(x + tw/2, baseline - (font.metrics("ascent")-font.metrics("descent"))/2, text=name, font=font, fill="#111")
            
            w, a, d = self.layout_row(n["arg"], size)
            h = a + d
            self.canvas.create_text(x + tw + size*0.1, baseline - a + h/2, text="(", font=(FONT_FAMILY, int((h/size)*size*0.9)), fill="#111")
            self.draw_row(n["arg"], x + tw + size*0.4, baseline, size)
            self.canvas.create_text(x + tw + w + size*0.6, baseline - a + h/2, text=")", font=(FONT_FAMILY, int((h/size)*size*0.9)), fill="#111")
            
        elif t == "chem":
            w, a, d = self.layout_row(n["body"], size)
            self.canvas.create_text(x + 2, baseline, text="chem", font=("TkDefaultFont", 8), fill="#777", anchor="w")
            self.draw_row(n["body"], x + size*1.5, baseline, size)
            
        elif t == "matrix":
            colw = [0, 0]; rowh = [0, 0]
            for ri, rr in enumerate(n["rows"]):
                for ci, cell in enumerate(rr):
                    w, a, d = self.layout_row(cell, size)
                    colw[ci] = max(colw[ci], w)
                    rowh[ri] = max(rowh[ri], a + d)
                    
            total_w = sum(colw) + size
            total_h = sum(rowh) + size * 0.5
            
            self.canvas.create_line(x+size*0.3, baseline-total_h*0.6, x+size*0.1, baseline-total_h*0.6, x+size*0.1, baseline+total_h*0.4, x+size*0.3, baseline+total_h*0.4, fill="#111", width=1.5)
            self.canvas.create_line(x+total_w-size*0.3, baseline-total_h*0.6, x+total_w-size*0.1, baseline-total_h*0.6, x+total_w-size*0.1, baseline+total_h*0.4, x+total_w-size*0.3, baseline+total_h*0.4, fill="#111", width=1.5)
            
            cy = baseline - total_h * 0.6 + size*0.25
            for ri, rr in enumerate(n["rows"]):
                cx = x + size*0.5
                for ci, cell in enumerate(rr):
                    w, a, d = self.layout_row(cell, size)
                    self.draw_row(cell, cx + (colw[ci]-w)/2, cy + a, size)
                    cx += colw[ci] + size*0.3
                cy += rowh[ri] + size*0.5
                
        elif t == "cases":
            max_w = 0; total_h = 0
            heights = []
            for rr in n["rows"]:
                w, a, d = self.layout_row(rr, size)
                max_w = max(max_w, w)
                h = a + d + size * 0.5
                heights.append(h)
                total_h += h
                
            first_w, first_a, first_d = self.layout_row(n["rows"][0], size)
            top_y = baseline - first_a - size * 0.1
            mid_y = top_y + total_h / 2
            
            brace_size = int(total_h / 1.4)
            brace_size = max(brace_size, int(size * 1.5))
            
            self.canvas.create_text(x + size*0.3, mid_y, text="{", font=(FONT_FAMILY, brace_size), fill="#111", anchor="center")
            
            cy = baseline
            for rr in n["rows"]:
                w, a, d = self.layout_row(rr, size)
                self.draw_row(rr, x + size*1.0, cy, size)
                cy += a + d + size * 0.5

    def _canvas_click(self, event):
        self.canvas.focus_set()
        best_dist = float('inf')
        best_target = None
        
        for (x0, y0, x1, y1, r, idx) in self.hit_boxes:
            if x0 - 5 <= event.x <= x1 + 5 and y0 - 5 <= event.y <= y1 + 5:
                if r is not None:
                    best_dist = 0
                    best_target = (r, idx)
                    break

        if not best_target:
            for (x0, y0, x1, y1, r, idx) in self.hit_boxes:
                if r is None: continue
                dist = abs(event.x - (x0+x1)/2) + abs(event.y - (y0+y1)/2)
                if dist < best_dist:
                    best_dist = dist
                    best_target = (r, idx)
                    
        if best_target:
            self._set_active(best_target[0], best_target[1])

    # ------------------ 导出逻辑 ------------------
    def _export_node(self, n):
        t = n["t"]
        if t == "symbol": return n["latex"]
        if t == "txt": return n["v"] if n.get("raw") else escape_text(n["v"])
        if t == "newline": return r" \\ "
        if t == "frac": return r"\frac{"+self._export_row(n["num"])+"}{"+self._export_row(n["den"])+"}"
        if t == "sqrt": return r"\sqrt{"+self._export_row(n["body"])+"}"
        if t == "sup": return "{"+self._export_row(n["base"])+"}^{"+self._export_row(n["exp"])+"}"
        if t == "sub": return "{"+self._export_row(n["base"])+"}_{"+self._export_row(n["sub"])+"}"
        if t == "subsup": return "{"+self._export_row(n["base"])+"}_{"+self._export_row(n["sub"])+"}^{"+self._export_row(n["sup"])+"}"
        if t == "paren": return r"\left("+self._export_row(n["body"])+r"\right)"
        if t == "abs": return r"\left|"+self._export_row(n["body"])+r"\right|"
        if t == "vec": return r"\vec{"+self._export_row(n["body"])+"}"
        if t == "bar": return r"\overline{"+self._export_row(n["body"])+"}"
        if t in ("sum","int","lim"):
            sym={"sum":r"\sum","int":r"\int","lim":r"\lim"}[t]
            a=self._export_row(n["sub"]); b=self._export_row(n["sup"])
            return sym+("_{" + a + "}" if a else "")+("^{" + b + "}" if b else "")
        if t == "func":
            name=n["name"]; prefix="\\"+name if name in FUNCTIONS else name
            return prefix+r"\left("+self._export_row(n["arg"])+r"\right)"
        if t == "chem": return r"\ce{"+self._export_row(n["body"])+"}"
        if t == "matrix": return r"\begin{pmatrix}"+r" \\ ".join(" & ".join(self._export_row(c) for c in rr0) for rr0 in n["rows"])+r"\end{pmatrix}"
        if t == "cases": return r"\begin{cases}"+r" \\ ".join(self._export_row(c) for c in n["rows"])+r"\end{cases}"
        return ""
        
    def _export_row(self, r):
        return "".join(self._export_node(n) for n in r["kids"])

    def export_latex(self):
        tex = self._export_row(self.root)
        # 清理因为空行或误操作导致的多余换行符
        tex = tex.replace("\\\\ \\\\", "\\\\").replace("\\\\  \\\\", "\\\\")
        tex = tex.strip(" \\\\")
        return tex

    def export_markdown(self):
        tex = self.export_latex()
        if not tex.strip(): return ""
        if "\\\\" in tex or "&" in tex:
            return "$$\n\\begin{aligned}\n" + tex + "\n\\end{aligned}\n$$\n"
        return "$$\n" + tex + "\n$$\n"

    def show_output(self):
        win=tk.Toplevel(self.win); win.title("生成的 Markdown / LaTeX"); win.geometry("760x460")
        ttk.Label(win,text="以下代码复制到支持 LaTeX 数学公式的 Markdown 环境中。化学公式需要 mhchem 扩展。",wraplength=700).pack(anchor="w",padx=12,pady=10)
        out=tk.Text(win,wrap="word",font=("Menlo",11),height=15)
        out.pack(fill="both",expand=True,padx=12,pady=4)
        out.insert("1.0",self.export_markdown())
        bar=ttk.Frame(win,padding=12); bar.pack(fill="x")
        def copy():
            self.win.clipboard_clear(); self.win.clipboard_append(out.get("1.0","end-1c"))
            self.status.config(text="已复制输出代码")
        ttk.Button(bar,text="复制",command=copy).pack(side="right")
        ttk.Button(bar,text="保存为 .md",command=lambda:self.export_md()).pack(side="right",padx=6)

    def copy_markdown(self):
        value=self.export_markdown()
        self.win.clipboard_clear(); self.win.clipboard_append(value)
        self.status.config(text="Markdown 代码已复制到剪贴板")
        self.canvas.focus_set()

    def export_md(self):
        path=filedialog.asksaveasfilename(defaultextension=".md",filetypes=[("Markdown","*.md"),("Text","*.txt")],initialfile="formula.md")
        if not path: return
        try:
            with open(path,"w",encoding="utf-8") as f:
                f.write(self.export_markdown())
            self.status.config(text="已保存："+path)
        except OSError as e:
            messagebox.showerror("保存失败",str(e))
        self.canvas.focus_set()

def main():
    window=tk.Tk()
    app=VisualLatexApp(window)
    def update_tools(event=None):
        idx=app.tabs.index(app.tabs.select())
        app._show_tools(idx)
    app.tabs.bind("<<NotebookTabChanged>>", update_tools)
    window.mainloop()

if __name__ == "__main__":
    main()